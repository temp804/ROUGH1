"""
Universal Video Downloader & Media Extractor (Streamlit + yt-dlp)
Supports 1000+ platforms (YouTube, adult websites, social media, generic hosts)
Includes security bypass options: User-Agent spoofing, cookies injection, proxy, and custom headers.
"""

import os
import sys
import subprocess
import time
import tempfile
import threading
import socket
import json
import uuid
import random
import io
import base64
import http.server
import socketserver
import urllib.parse
from typing import Dict, Any, Optional
import streamlit as st
import qrcode

# Configure page settings
st.set_page_config(
    page_title="Universal Video Downloader Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aggressive branding lockdown — hides all Streamlit icons + blocks badge taps
st.markdown("""
<style>
    /* 1. Hide the core header container across both mobile and desktop structures */
    header[data-testid="stHeader"],
    .stHeader,
    div[class*="stHeader"] {
        visibility: hidden !important;
        display: none !important;
        opacity: 0 !important;
        height: 0px !important;
        min-height: 0px !important;
        pointer-events: none !important;
        overflow: hidden !important;
    }

    /* 2. Target specific deployment badges and profile icons */
    div[data-testid="stAppDeployButton"],
    div[class*="viewerBadge"],
    span[class*="viewerBadge"],
    a[class*="viewerBadge"],
    .viewerBadge_container__1QSob,
    .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK,
    .styles_viewerBadge__1yB5_,
    header a,
    header button,
    [data-testid="stHeaderActionElements"],
    [data-testid="stToolbar"],
    [data-testid="stStatusWidget"],
    [data-testid="stDecoration"],
    [data-testid="manage-app-button"],
    [data-testid="stAppDeployButton"],
    [data-testid="stActionButtonIcon"],
    .stAppDeployButton,
    #stDecoration {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* 3. Block external badge links (the streamlit.app redirect URL) */
    a[href*="github.com"],
    a[href*="share.streamlit.io/user"],
    a[href*="streamlit.app"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* 4. Strip the default Streamlit footer and hamburger menu */
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}

    /* 5. FAIL-SAFE: Invisible physical wall at the bottom-right corner.
       Intercepts ALL clicks/touches before they reach the badge underneath.
       pointer-events: auto swallows the tap — nothing gets through. */
    body::after {
        content: "";
        position: fixed;
        bottom: 0;
        right: 0;
        width: 200px;
        height: 80px;
        background: transparent !important;
        z-index: 2147483647 !important;
        pointer-events: auto !important;
        display: block;
    }

    /* ── 6. REMOVE TOP PADDING (since header is now 0px height) ── */
    .block-container {
        padding-top: 1.5rem !important;
    }

    /* ── App styles ── */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FF4B4B, #FF8F00, #4A90E2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #888888;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #1E2229;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #2D3139;
        margin-bottom: 10px;
    }
    .quality-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        background-color: #FF4B4B22;
        color: #FF4B4B;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .stProgress > div > div > div > div {
        background-color: #FF4B4B;
    }
    .share-pin-box {
        text-align: center;
        padding: 24px 20px;
        background: linear-gradient(145deg, #1A1D24, #13151A);
        border-radius: 14px;
        border: 2px solid #FF4B4B44;
        box-shadow: 0 8px 30px rgba(0,0,0,0.4);
        margin: 15px 0 25px 0;
    }
    .share-pin-code {
        font-size: 3.6rem;
        font-weight: 800;
        letter-spacing: 12px;
        color: #FF4B4B;
        font-family: 'Consolas', 'Courier New', monospace;
        margin: 8px 0;
        text-shadow: 0 0 20px rgba(255, 75, 75, 0.4);
    }
    .share-file-card {
        background: #1E2229;
        border-radius: 10px;
        border: 1px solid #2D3139;
        padding: 16px 20px;
        margin-bottom: 15px;
    }
    @media (max-width: 600px) {
        .share-pin-code {
            font-size: 2.3rem !important;
            letter-spacing: 6px !important;
        }
        .share-pin-box {
            padding: 16px 10px !important;
        }
        .share-file-card {
            padding: 12px 14px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ── NEUTRALIZE VIEWER BADGE (hide it + disable click if it stays visible) ──
import streamlit.components.v1 as _components
_components.html("""
<script>
(function() {
    function neutralizeViewerBadge() {
        try {
            var doc = window.parent.document;

            // ── STRATEGY 1: Hide by class wildcard ──
            doc.querySelectorAll('[class*="viewerBadge"]').forEach(function(el) {
                el.style.setProperty('display', 'none', 'important');
                el.style.setProperty('visibility', 'hidden', 'important');
                el.style.setProperty('pointer-events', 'none', 'important');
                if (el.parentElement) {
                    el.parentElement.style.setProperty('display', 'none', 'important');
                }
            });

            // ── STRATEGY 2: Find all <a> tags linking to github/streamlit profile ──
            doc.querySelectorAll('a').forEach(function(a) {
                var href = a.getAttribute('href') || '';
                if (href.indexOf('github.com') !== -1 || href.indexOf('share.streamlit.io/user') !== -1) {
                    // Try to hide
                    a.style.setProperty('display', 'none', 'important');
                    var p = a.parentElement;
                    if (p) p.style.setProperty('display', 'none', 'important');
                    // Fallback: neutralize the click even if it stays visible
                    a.removeAttribute('href');
                    a.removeAttribute('target');
                    a.style.setProperty('pointer-events', 'none', 'important');
                    a.style.setProperty('cursor', 'default', 'important');
                    a.addEventListener('click', function(e) { e.preventDefault(); e.stopPropagation(); return false; }, true);
                }
            });

            // ── STRATEGY 3: Hide avatar images (GitHub profile pictures) ──
            doc.querySelectorAll('img').forEach(function(img) {
                var src = img.getAttribute('src') || '';
                if (src.indexOf('githubusercontent.com') !== -1 || src.indexOf('avatars') !== -1) {
                    var anchor = img.closest('a') || img.parentElement;
                    if (anchor) {
                        anchor.style.setProperty('display', 'none', 'important');
                        anchor.removeAttribute('href');
                        anchor.style.setProperty('pointer-events', 'none', 'important');
                        anchor.addEventListener('click', function(e) { e.preventDefault(); e.stopPropagation(); return false; }, true);
                    }
                    img.style.setProperty('display', 'none', 'important');
                }
            });

            // ── STRATEGY 4: Block all fixed-position bottom-right clickable elements ──
            doc.querySelectorAll('a, button').forEach(function(el) {
                var rect = el.getBoundingClientRect();
                var winW = window.parent.innerWidth;
                var winH = window.parent.innerHeight;
                // If element is in bottom-right quadrant and small (badge-like)
                if (rect.right > winW * 0.6 && rect.bottom > winH * 0.7 &&
                    rect.width < 80 && rect.height < 80 && rect.width > 0) {
                    var href = el.getAttribute('href') || '';
                    // Only neutralize external links (not our app links)
                    if (href.indexOf('streamlit.io') !== -1 || href.indexOf('github.com') !== -1) {
                        el.removeAttribute('href');
                        el.style.setProperty('pointer-events', 'none', 'important');
                        el.addEventListener('click', function(e) { e.preventDefault(); e.stopPropagation(); return false; }, true);
                    }
                }
            });

        } catch(e) {}
    }

    // Run immediately and at multiple delays (badge loads async)
    neutralizeViewerBadge();
    [100, 300, 500, 800, 1000, 1500, 2000, 3000, 5000].forEach(function(t) {
        setTimeout(neutralizeViewerBadge, t);
    });

    // MutationObserver: re-run whenever DOM changes
    try {
        var observer = new MutationObserver(function() { neutralizeViewerBadge(); });
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
    } catch(e) {}
})();
</script>
""", height=0, scrolling=False)


try:
    import yt_dlp
    # Hotpatch for modern XHamster layout (resolves KeyError('title') on mirror and new site structures)
    try:
        import yt_dlp.extractor.xhamster as xh
        orig_extract = xh.XHamsterIE._real_extract
        def patched_xhamster_extract(self, url):
            orig_parse_json = self._parse_json
            def patched_parse_json(json_string, video_id, *args, **kwargs):
                data = orig_parse_json(json_string, video_id, *args, **kwargs)
                if isinstance(data, dict) and 'videoModel' in data:
                    if 'title' not in data['videoModel']:
                        data['videoModel']['title'] = (
                            data.get('videoHeading', {}).get('title')
                            or data.get('videoEntity', {}).get('title')
                            or data.get('xplayerSettings', {}).get('title')
                            or 'Video'
                        )
                return data
            self._parse_json = patched_parse_json
            return orig_extract(self, url)
        xh.XHamsterIE._real_extract = patched_xhamster_extract
    except Exception:
        pass
except ImportError:
    st.error("⚠️ `yt-dlp` is not installed. Please run `pip install yt-dlp` in your terminal.")
    st.stop()

# Check for curl-cffi browser impersonation support (bypasses Cloudflare / JA3 TLS bot checks)
try:
    import curl_cffi
    from yt_dlp.networking.impersonate import ImpersonateTarget
    IMPERSONATE_AVAILABLE = True
except Exception:
    IMPERSONATE_AVAILABLE = False

import shutil
FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None

# Ensure default downloads directory exists
DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# ----------------- SIDEBAR: NETWORK & BYPASS CONFIG -----------------
st.sidebar.title("🛡️ Bypass & Network Settings")
st.sidebar.caption("Configure headers, cookies, TLS impersonation, and proxies to overcome bot detection, Cloudflare, and age restrictions.")

if IMPERSONATE_AVAILABLE:
    st.sidebar.success("🛡️ **Cloudflare Impersonation Ready** (`curl-cffi` active)")
else:
    st.sidebar.warning("⚠️ **curl-cffi not found.** Install with `pip install curl-cffi` for Cloudflare bypass.")

if not FFMPEG_AVAILABLE:
    st.sidebar.warning("⚠️ **FFmpeg is not installed.** Most single-file video streams work automatically. For merging YouTube 1080p+ split audio/video streams, install FFmpeg (e.g. `winget install Gyan.FFmpeg`).")
else:
    st.sidebar.success("✅ **FFmpeg detected** (Full audio+video merging supported)")

IMPERSONATE_PROFILES = {
    "Safari (iOS 17.2 iPhone - Best for Cloudflare / Mobile)": {
        "target": "safari-17.2:ios-17.2",
        "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
    },
    "Safari (iOS 18.0 iPhone)": {
        "target": "safari-18.0:ios-18.0",
        "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
    },
    "Safari 18 (macOS Sonoma)": {
        "target": "safari-18.0:macos-15",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
    },
    "Chrome 131 (Android 14 Mobile)": {
        "target": "chrome-131:android-14",
        "ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
    },
    "Chrome 116 (Windows 10/11 Desktop)": {
        "target": "chrome-116:windows-10",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    },
    "Chrome 131 (macOS Desktop)": {
        "target": "chrome-131:macos-14",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    },
    "Firefox 135 (macOS Desktop)": {
        "target": "firefox-135:macos-14",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) Gecko/20100101 Firefox/135.0"
    },
    "Edge 101 (Windows Desktop)": {
        "target": "edge-101:windows-10",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47"
    },
}

with st.sidebar.expander("⚡ Cloudflare & TLS Impersonation (Bypass 403)", expanded=True):
    enable_impersonate = st.checkbox("Enable TLS Browser Impersonation", value=IMPERSONATE_AVAILABLE, disabled=not IMPERSONATE_AVAILABLE)
    profile_choice = st.selectbox(
        "Browser Fingerprint (JA3/JA4 TLS Emulation)",
        list(IMPERSONATE_PROFILES.keys()),
        index=0,
        disabled=not enable_impersonate
    )
    selected_profile = IMPERSONATE_PROFILES[profile_choice]
    st.caption("✨ Matches mobile Safari / desktop TLS ciphers & HTTP/2 handshakes to pass Cloudflare bot detection.")

with st.sidebar.expander("🌐 User-Agent & Headers", expanded=False):
    auto_sync_ua = st.checkbox("Auto-sync User-Agent with TLS Fingerprint", value=True)
    if auto_sync_ua and enable_impersonate:
        user_agent_str = selected_profile["ua"]
        st.info(f"Synchronized User-Agent: `{user_agent_str[:50]}...`")
    else:
        ua_preset = st.selectbox(
            "User-Agent Preset",
            [
                "Safari (iPhone Mobile)",
                "Chrome 125 (Windows 11)",
                "Safari 17 (macOS Sonoma)",
                "Firefox 126 (Windows 11)",
                "Chrome 125 (Android 14)",
                "Custom User-Agent"
            ]
        )
        ua_map = {
            "Safari (iPhone Mobile)": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Chrome 125 (Windows 11)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Safari 17 (macOS Sonoma)": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
            "Firefox 126 (Windows 11)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
            "Chrome 125 (Android 14)": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36",
        }
        if ua_preset == "Custom User-Agent":
            user_agent_str = st.text_input("Custom User-Agent String", value=ua_map["Safari (iPhone Mobile)"])
        else:
            user_agent_str = ua_map[ua_preset]

    custom_referer = st.text_input("Custom Referer URL (optional)", placeholder="e.g. https://www.google.com/")
    accept_language = st.text_input("Accept-Language", value="en-US,en;q=0.9")

with st.sidebar.expander("🍪 Cookie & Session Bypass", expanded=False):
    st.caption("Needed for age-gated sites, Cloudflare clearance, and member-only media.")
    cookie_mode = st.radio("Cookie Source", ["None", "Upload cookies.txt", "Extract from Local Browser"], index=0)

    cookie_file_path = None
    browser_name = None

    if cookie_mode == "Upload cookies.txt":
        uploaded_cookie = st.file_uploader("Upload exported Netscape cookies.txt", type=["txt"])
        if uploaded_cookie is not None:
            # Save temporary cookie file
            tmp_cookie = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            tmp_cookie.write(uploaded_cookie.getvalue())
            tmp_cookie.close()
            cookie_file_path = tmp_cookie.name
            st.success("✅ Cookies loaded")
    elif cookie_mode == "Extract from Local Browser":
        browser_name = st.selectbox("Select Browser", ["chrome", "firefox", "edge", "brave", "opera", "vivaldi"])
        st.info(f"Will attempt reading session cookies from {browser_name.title()}. (Requires browser to be closed or unlocked).")

# OpenGW / VPNGate SSTP Relay Node Pool (Port 443, MS-CHAPv2, user: vpn, pass: vpn)
OPENGW_SERVERS = [
    "public-vpn-202.opengw.net",
    "public-vpn-200.opengw.net",
    "public-vpn-159.opengw.net",
    "vpn801875041.opengw.net",
    "public-vpn-230.opengw.net",
    "opengw.opengw.net",
    "vpn650277207.opengw.net",
    "vpn864131273.opengw.net",
]

def get_windows_vpn_status() -> tuple[bool, str]:
    """Check if Windows has an active rasdial / SSTP VPN connection."""
    if sys.platform != "win32":
        return False, "Non-Windows OS"
    try:
        res = subprocess.run(["rasdial"], capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and "Connected to" in res.stdout:
            lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            conn_names = []
            capture = False
            for line in lines:
                if line.startswith("Connected to"):
                    capture = True
                    continue
                if line.startswith("Command completed"):
                    break
                if capture:
                    conn_names.append(line)
            if conn_names:
                return True, ", ".join(conn_names)
            return True, "Active"
        return False, "Disconnected"
    except Exception:
        return False, "Unavailable"

with st.sidebar.expander("🔒 SSTP VPN Gateway (Mobile & Laptop)", expanded=True):
    # System SSTP connection status
    vpn_connected, active_vpn_name = get_windows_vpn_status()
    if vpn_connected:
        st.success(f"🟢 **SSTP VPN Active:** `{active_vpn_name}`")
        st.caption("📱 💻 **Full Gateway Protected**: All downloads requested from mobile phones or laptops flow through SSTP.")
    else:
        st.caption("⚪ **SSTP VPN Status:** Standby / Disconnected")

    proxy_mode = st.selectbox(
        "SSTP VPN / Proxy Mode",
        [
            "1-Click SSTP Gateway (Works for Mobile & Laptop)",
            "Auto-Failover SSTP Proxy Pool (Port 443, vpn:vpn)",
            "Specific SSTP Node (Port 443, vpn:vpn)",
            "📱 Direct Mobile Phone SSTP Setup (Android & iPhone)",
            "Custom Proxy URL",
            "None (Direct Connection / System VPN Active)"
        ],
        index=0
    )

    proxy_protocol = "http"
    proxy_port = "443"
    proxy_user = "vpn"
    proxy_pass = "vpn"
    active_proxies = []

    if proxy_mode == "1-Click SSTP Gateway (Works for Mobile & Laptop)":
        st.markdown("""
        **📱 Mobile & 💻 Laptop One-Tap SSTP Gateway**  
        Tap connect below from any device (phone, tablet, or laptop). It dials OpenGW over SSTP (Port 443) using credentials `vpn` and `vpn`.
        - **Tunnel Type:** SSTP (Port 443 - MS-CHAPv2)
        - **Username:** `vpn`
        - **Password:** `vpn`
        - **Universal Access:** Any phone or computer using this app gets unblocked high-speed streams automatically!
        """)

        target_sstp_srv = st.selectbox("Select SSTP Relay Node", OPENGW_SERVERS, index=0)
        
        col_vpn_conn, col_vpn_disc = st.columns(2)
        with col_vpn_conn:
            if st.button("🚀 Connect SSTP VPN", type="primary", use_container_width=True):
                with st.spinner(f"Connecting SSTP to `{target_sstp_srv}` with `vpn:vpn`..."):
                    ps_cmd = (
                        f'Add-VpnConnection -Name "OpenGW-SSTP" -ServerAddress "{target_sstp_srv}" '
                        f'-TunnelType Sstp -AuthenticationMethod MSChapv2 -SplitTunneling:$false -Force; '
                        f'rasdial "OpenGW-SSTP" vpn vpn'
                    )
                    try:
                        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=25)
                        if "Connected to" in res.stdout or "Command completed successfully" in res.stdout:
                            st.success(f"✅ SSTP VPN Connected to `{target_sstp_srv}`! Mobile & Laptop traffic is now bypassed.")
                        else:
                            st.info(f"Result: {res.stdout.strip() or res.stderr.strip()}")
                    except Exception as err:
                        st.error(f"Connection failed: {str(err)}")
                    st.rerun()

        with col_vpn_disc:
            if st.button("⏹️ Disconnect VPN", use_container_width=True):
                try:
                    subprocess.run(["rasdial", "OpenGW-SSTP", "/disconnect"], capture_output=True, text=True)
                    if vpn_connected and active_vpn_name:
                        subprocess.run(["rasdial", active_vpn_name, "/disconnect"], capture_output=True, text=True)
                    st.success("VPN Disconnected.")
                except Exception as err:
                    st.error(f"Disconnect error: {str(err)}")
                st.rerun()

        st.caption("PowerShell Command:")
        st.code(f'rasdial "OpenGW-SSTP" vpn vpn', language="powershell")

    elif proxy_mode == "Auto-Failover SSTP Proxy Pool (Port 443, vpn:vpn)":
        st.info("🛡️ **SSTP Tunnel Active**: Connecting through port 443 with credentials `username: vpn` and `password: vpn`. If the primary node fails, automatically fails over across 8 OpenGW SSTP nodes.")
        col_prot, col_pt = st.columns(2)
        with col_prot:
            proxy_protocol = st.selectbox("Tunnel Protocol", ["http", "https", "socks5"], index=0, help="HTTP CONNECT or HTTPS tunnel via SSTP port 443")
        with col_pt:
            proxy_port = st.text_input("Port (SSTP Standard)", value="443")

        col_u, col_p = st.columns(2)
        with col_u:
            proxy_user = st.text_input("Username", value="vpn")
        with col_p:
            proxy_pass = st.text_input("Password", value="vpn", type="password")

        # Generate list of SSTP proxy strings in failover order
        for srv in OPENGW_SERVERS:
            active_proxies.append(f"{proxy_protocol}://{proxy_user}:{proxy_pass}@{srv}:{proxy_port}")

    elif proxy_mode == "Specific SSTP Node (Port 443, vpn:vpn)":
        selected_srv = st.selectbox("Select SSTP Server", OPENGW_SERVERS)
        col_prot, col_pt = st.columns(2)
        with col_prot:
            proxy_protocol = st.selectbox("Protocol", ["http", "https", "socks5"], index=0)
        with col_pt:
            proxy_port = st.text_input("Port", value="443")

        col_u, col_p = st.columns(2)
        with col_u:
            proxy_user = st.text_input("Username", value="vpn", key="spec_u")
        with col_p:
            proxy_pass = st.text_input("Password", value="vpn", type="password", key="spec_p")

        configured_proxy = f"{proxy_protocol}://{proxy_user}:{proxy_pass}@{selected_srv}:{proxy_port}"
        active_proxies.append(configured_proxy)
        st.caption(f"Configured: `{configured_proxy}`")

    elif proxy_mode == "📱 Direct Mobile Phone SSTP Setup (Android & iPhone)":
        st.markdown("""
        ### 📱 Direct Mobile Phone SSTP Connection
        You can connect your phone directly to the OpenGW SSTP VPN network:
        
        **1. Connection Settings for Your Phone:**
        - **Server Address:** `public-vpn-202.opengw.net` (or `public-vpn-200.opengw.net`)
        - **Port:** `443`
        - **Username:** `vpn`
        - **Password:** `vpn`
        - **Tunnel Type:** `SSTP` (MS-CHAPv2, No cert verification needed)
        
        **2. Free Mobile Apps:**
        - **Android:** Download **SSTP VPN Client** (by Masaaki) from Google Play Store or **OpenVPN for Android**.
        - **iOS (iPhone):** Download **OpenVPN Connect** or **SSTP Client** from the App Store.
        
        **3. Tap Connect:** Your entire mobile browser, YouTube app, and download streams are encrypted and bypassed!
        """)
        st.code("Server: public-vpn-202.opengw.net\nPort: 443\nUsername: vpn\nPassword: vpn", language="text")

    elif proxy_mode == "Custom Proxy URL":
        custom_p = st.text_input("Proxy URL", placeholder="http://vpn:vpn@public-vpn-202.opengw.net:443")
        if custom_p.strip():
            active_proxies.append(custom_p.strip())

    elif proxy_mode == "None (Direct Connection / System VPN Active)":
        active_proxies = []
        if vpn_connected:
            st.info(f"🚀 Using active system SSTP VPN tunnel (`{active_vpn_name}`) — protecting all mobile & laptop streams.")
        else:
            st.caption("Using direct internet connection without proxy/VPN.")

    socket_timeout = st.slider("Socket Timeout (seconds)", min_value=5, max_value=60, value=20)
    retries = st.slider("Max Connection Retries", min_value=1, max_value=20, value=5)
    fragment_retries = st.slider("HLS/DASH Fragment Retries", min_value=1, max_value=30, value=15)
    rate_limit = st.text_input("Rate Limit (optional, e.g. 5M, 500K)", placeholder="Unlimited")

# ----------------- 5GB SEND/RECEIVE FILE SHARING SUBSYSTEM -----------------
SHARED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_files")
os.makedirs(SHARED_DIR, exist_ok=True)
REGISTRY_FILE = os.path.join(SHARED_DIR, "shares_registry.json")

class FileShareManager:
    _lock = threading.Lock()

    @staticmethod
    def _load_registry() -> Dict[str, Any]:
        if not os.path.exists(REGISTRY_FILE):
            return {}
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _save_registry(data: Dict[str, Any]):
        try:
            with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @classmethod
    def generate_unique_code(cls) -> str:
        with cls._lock:
            reg = cls._load_registry()
            for _ in range(100):
                c = f"{random.randint(100000, 999999)}"
                if c not in reg:
                    return c
            return str(int(time.time()))[-6:]

    @classmethod
    def create_share(cls, filepath: str = None, filename: str = None, expiry_seconds: int = 3600,
                     one_time: bool = False, delete_on_expiry: bool = True, text_content: str = None) -> Dict[str, Any]:
        with cls._lock:
            reg = cls._load_registry()
            code = f"{random.randint(100000, 999999)}"
            while code in reg:
                code = f"{random.randint(100000, 999999)}"
            
            share_id = uuid.uuid4().hex[:12]
            size = os.path.getsize(filepath) if (filepath and os.path.exists(filepath)) else (len(text_content.encode('utf-8')) if text_content else 0)
            
            entry = {
                "code": code,
                "id": share_id,
                "type": "text" if text_content is not None else "file",
                "filename": filename or (os.path.basename(filepath) if filepath else "shared_text.txt"),
                "filepath": os.path.abspath(filepath) if filepath else None,
                "size": size,
                "created_at": time.time(),
                "expires_at": time.time() + expiry_seconds,
                "one_time": one_time,
                "delete_on_expiry": delete_on_expiry,
                "downloads": 0,
                "text_content": text_content
            }
            reg[code] = entry
            cls._save_registry(reg)
            return entry

    @classmethod
    def get_share(cls, code_or_id: str) -> Optional[Dict[str, Any]]:
        clean = code_or_id.strip().replace(" ", "").replace("-", "")
        with cls._lock:
            reg = cls._load_registry()
            entry = reg.get(clean)
            if not entry:
                for k, v in reg.items():
                    if v.get("id") == clean:
                        entry = v
                        break
            if not entry:
                return None
            if time.time() > entry.get("expires_at", 0):
                cls._delete_share_unlocked(reg, entry.get("code"))
                return None
            return entry

    @classmethod
    def record_download(cls, code: str):
        with cls._lock:
            reg = cls._load_registry()
            if code in reg:
                reg[code]["downloads"] = reg[code].get("downloads", 0) + 1
                if reg[code].get("one_time") and reg[code]["downloads"] >= 1:
                    cls._delete_share_unlocked(reg, code)
                else:
                    cls._save_registry(reg)

    @classmethod
    def delete_share(cls, code: str):
        with cls._lock:
            reg = cls._load_registry()
            cls._delete_share_unlocked(reg, code)

    @classmethod
    def _delete_share_unlocked(cls, reg: dict, code: str):
        if code in reg:
            entry = reg.pop(code)
            if entry.get("delete_on_expiry") and entry.get("filepath") and os.path.exists(entry["filepath"]):
                try:
                    os.remove(entry["filepath"])
                except Exception:
                    pass
            cls._save_registry(reg)

    @classmethod
    def get_all_active(cls) -> list:
        with cls._lock:
            reg = cls._load_registry()
            now = time.time()
            active = []
            expired = []
            for code, entry in reg.items():
                if now > entry.get("expires_at", 0):
                    expired.append(code)
                else:
                    active.append(entry)
            for code in expired:
                cls._delete_share_unlocked(reg, code)
            return sorted(active, key=lambda x: x.get("created_at", 0), reverse=True)

    @classmethod
    def cleanup_expired_shares(cls):
        with cls._lock:
            reg = cls._load_registry()
            now = time.time()
            expired = [c for c, e in reg.items() if now > e.get("expires_at", 0)]
            for c in expired:
                cls._delete_share_unlocked(reg, c)

class ResumableFileServerHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) >= 2 and parts[0] == "dl":
            key = parts[1]
            entry = FileShareManager.get_share(key)
            if entry and entry.get("filepath") and os.path.exists(entry["filepath"]):
                return os.path.abspath(entry["filepath"])
        return super().translate_path(path)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) >= 2 and parts[0] == "dl":
            key = parts[1]
            entry = FileShareManager.get_share(key)
            if not entry:
                self.send_error(404, "Sharing code expired or invalid.")
                return
            FileShareManager.record_download(entry.get("code"))
        return super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.strip("/") == "upload":
            try:
                q = urllib.parse.parse_qs(parsed.query)
                raw_fname = q.get("filename", ["uploaded_file.bin"])[0]
                filename = urllib.parse.unquote(raw_fname)

                # Content-Length may be missing (chunked transfer from mobile browsers)
                cl_header = self.headers.get("Content-Length") or self.headers.get("content-length")
                content_len = int(cl_header) if cl_header else -1  # -1 = unknown, read until EOF

                safe_fname = filename.replace(" ", "_")
                # Use a temp name first so we can register after writing
                tmp_code = uuid.uuid4().hex[:8]
                dest_path = os.path.join(SHARED_DIR, f"tmp_{tmp_code}_{safe_fname}")

                bytes_read = 0
                chunk_size = 256 * 1024  # 256KB chunks for better large-file throughput

                with open(dest_path, "wb") as f_out:
                    if content_len > 0:
                        # Known size: read exactly content_len bytes
                        remaining = content_len
                        while remaining > 0:
                            to_read = min(remaining, chunk_size)
                            chunk = self.rfile.read(to_read)
                            if not chunk:
                                break
                            f_out.write(chunk)
                            remaining -= len(chunk)
                            bytes_read += len(chunk)
                    else:
                        # Unknown size (chunked / mobile): read until connection closes
                        while True:
                            chunk = self.rfile.read(chunk_size)
                            if not chunk:
                                break
                            f_out.write(chunk)
                            bytes_read += len(chunk)

                # Register share (generates a clean 6-digit code)
                share_entry = FileShareManager.create_share(
                    filepath=dest_path,
                    filename=filename,
                    expiry_seconds=3600,
                    one_time=False,
                    delete_on_expiry=True
                )
                code = share_entry["code"]

                resp_data = json.dumps({
                    "status": "success",
                    "code": code,
                    "filename": filename,
                    "size": bytes_read
                }).encode("utf-8")

                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "*")
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_data)))
                self.end_headers()
                self.wfile.write(resp_data)
                return
            except Exception as e:
                try:
                    self.send_error(500, str(e))
                except Exception:
                    pass
                return
        return self.send_error(404, "Not found")

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        parsed = urllib.parse.urlparse(self.path)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) >= 2 and parts[0] == "dl":
            key = parts[1]
            entry = FileShareManager.get_share(key)
            if entry and entry.get("filename"):
                safe_name = urllib.parse.quote(entry['filename'])
                self.send_header("Content-Disposition", f'attachment; filename="{entry["filename"]}"; filename*=UTF-8\'\'{safe_name}')
        super().end_headers()

    def log_message(self, format, *args):
        pass

def get_local_network_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_effective_host_ip() -> str:
    """Dynamically determine the host IP that the client used to access the app."""
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers") and st.context.headers:
            host_h = st.context.headers.get("host") or st.context.headers.get("Host")
            if host_h:
                h_only = host_h.split(":")[0].strip()
                if h_only and h_only not in ("localhost", "127.0.0.1", "0.0.0.0"):
                    return h_only
    except Exception:
        pass
    return get_local_network_ip()

def generate_qr_code_image_bytes(data_url: str) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=7,
        border=2,
    )
    qr.add_data(data_url)
    qr.make(fit=True)
    buf = io.BytesIO()
    try:
        # Explicitly request Pillow renderer — supports custom colors + format= kwarg
        from qrcode.image.pil import PilImage
        img = qr.make_image(image_factory=PilImage,
                            fill_color=(255, 75, 75),
                            back_color=(30, 34, 41))
        img.save(buf, format="PNG")
    except Exception:
        # Fallback: pure PyPNG renderer (no format kwarg, monochrome)
        img = qr.make_image()
        img.save(buf)
    buf.seek(0)
    return buf.getvalue()

_FILE_SERVER_PORT = None
_SERVER_START_LOCK = threading.Lock()

def ensure_file_server_running() -> int:
    global _FILE_SERVER_PORT
    with _SERVER_START_LOCK:
        if _FILE_SERVER_PORT is not None:
            return _FILE_SERVER_PORT
        port = 8504
        for p in range(8504, 8530):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", p))
                    port = p
                    break
            except OSError:
                continue
        try:
            httpd = socketserver.ThreadingTCPServer(("", port), ResumableFileServerHandler)
            t = threading.Thread(target=httpd.serve_forever, daemon=True)
            t.start()
            _FILE_SERVER_PORT = port
        except Exception:
            _FILE_SERVER_PORT = 8504

        def cleanup_loop():
            while True:
                time.sleep(45)
                try:
                    FileShareManager.cleanup_expired_shares()
                except Exception:
                    pass
        t_clean = threading.Thread(target=cleanup_loop, daemon=True)
        t_clean.start()

        return _FILE_SERVER_PORT

def stream_upload_to_disk(uploaded_file, dest_path, progress_bar=None, status_text=None) -> int:
    total_written = 0
    chunk_size = 8 * 1024 * 1024  # 8MB chunk buffer
    file_size = getattr(uploaded_file, "size", 0) or 0
    start_time = time.time()

    with open(dest_path, "wb") as f_out:
        while True:
            chunk = uploaded_file.read(chunk_size)
            if not chunk:
                break
            f_out.write(chunk)
            total_written += len(chunk)
            elapsed = max(0.001, time.time() - start_time)
            speed_mb = (total_written / (1024 * 1024)) / elapsed
            if file_size > 0 and progress_bar:
                pct = min(1.0, total_written / file_size)
                progress_bar.progress(pct)
                if status_text:
                    status_text.text(f"Streaming to disk: {format_bytes_human(total_written)} / {format_bytes_human(file_size)} ({speed_mb:.1f} MB/s)")

    if progress_bar:
        progress_bar.progress(1.0)
    return total_written

def get_file_chunk_generator(filepath, chunk_size=4*1024*1024):
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def format_bytes_human(size_bytes: int) -> str:
    if not size_bytes or size_bytes < 0:
        return "0 B"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

# Launch background resumable file streaming server
STREAM_PORT = ensure_file_server_running()
LOCAL_IP = get_local_network_ip()

# ----------------- HELPER FUNCTIONS -----------------

def build_ydl_opts(
    quality: str,
    output_template: str,
    proxy: Optional[str] = None,
    progress_hook=None,
    extra_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Build yt-dlp extraction/download options dictionary."""
    headers = {
        "User-Agent": user_agent_str,
        "Accept-Language": accept_language,
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    }
    if custom_referer:
        headers["Referer"] = custom_referer
    if extra_headers:
        headers.update(extra_headers)

    # Format selector based on resolution choice
    if quality == "Audio Only (MP3/M4A)":
        format_spec = "bestaudio/best"
        postprocessors = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif quality == "Best Available (Highest)":
        format_spec = "bestvideo+bestaudio/best"
        postprocessors = []
    elif quality == "1080p (Full HD)":
        format_spec = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
        postprocessors = []
    elif quality == "720p (HD)":
        format_spec = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
        postprocessors = []
    elif quality == "480p (SD)":
        format_spec = "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
        postprocessors = []
    elif quality == "360p":
        format_spec = "bestvideo[height<=360]+bestaudio/best[height<=360]/best"
        postprocessors = []
    elif quality == "240p (Low)":
        format_spec = "bestvideo[height<=240]+bestaudio/best[height<=240]/best"
        postprocessors = []
    else:
        format_spec = "bestvideo+bestaudio/best"
        postprocessors = []

    opts = {
        'format': format_spec,
        'outtmpl': output_template,
        'http_headers': headers,
        'socket_timeout': socket_timeout,
        'retries': retries,
        'fragment_retries': fragment_retries,
        'quiet': True,
        'no_warnings': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'ignoreerrors': False,
        'merge_output_format': 'mp4' if quality != "Audio Only (MP3/M4A)" else None,
    }

    if quality != "Audio Only (MP3/M4A)":
        postprocessors.append({
            'key': 'FFmpegVideoRemuxer',
            'preferedformat': 'mp4',
        })
        opts['postprocessor_args'] = {
            'merger': ['-movflags', '+faststart'],
            'videoremuxer': ['-movflags', '+faststart'],
        }

    if postprocessors:
        opts['postprocessors'] = postprocessors

    if enable_impersonate and IMPERSONATE_AVAILABLE:
        try:
            target = ImpersonateTarget.from_str(selected_profile["target"])
            opts['impersonate'] = target
        except Exception:
            pass

    if proxy:
        opts['proxy'] = proxy

    if rate_limit and rate_limit.strip():
        opts['ratelimit'] = rate_limit.strip()

    if cookie_mode == "Upload cookies.txt" and cookie_file_path:
        opts['cookiefile'] = cookie_file_path
    elif cookie_mode == "Extract from Local Browser" and browser_name:
        opts['cookiesfrombrowser'] = (browser_name,)

    if progress_hook:
        opts['progress_hooks'] = [progress_hook]

    return opts

def get_url_candidates(raw_url: str) -> list[str]:
    """Preserve exact input URL to respect unblocked local mirrors (e.g. xhamster46.desi)."""
    url = raw_url.strip()
    return [url]

def fallback_generic_extractor(url: str, current_proxy: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Intelligent fallback scraper for unlisted websites (extracts title, thumbnail, embed iframes, and direct streams)."""
    import urllib.request
    import re
    import html as html_lib

    headers = {
        'User-Agent': user_agent_str,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': accept_language,
    }
    if custom_referer:
        headers['Referer'] = custom_referer

    handlers = []
    if current_proxy:
        handlers.append(urllib.request.ProxyHandler({'http': current_proxy, 'https': current_proxy}))
    opener = urllib.request.build_opener(*handlers)

    req = urllib.request.Request(url, headers=headers)
    try:
        with opener.open(req, timeout=12) as resp:
            page_html = resp.read().decode('utf-8', errors='ignore')
    except Exception:
        return None

    # Extract Title & Thumbnail
    title_m = re.search(r'<title>(.*?)</title>', page_html, re.IGNORECASE)
    raw_title = title_m.group(1).split(' - ')[0].strip() if title_m else 'Discovered Video Stream'
    title = html_lib.unescape(raw_title)

    thumb_m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', page_html, re.IGNORECASE)
    thumbnail = thumb_m.group(1) if thumb_m else None

    # Search for embedded host links (Streamtape, Dood, Mixdrop, Filemoon, etc.)
    embed_regexes = [
        r'https?://(?:www\.)?(?:streamtape\.com|streamta\.pe|dood\.(?:to|so|ws|pm|li)|doodstream\.com|mixdrop\.(?:co|to|sx)|voe\.sx|filemoon\.(?:sx|to)|streamwish\.(?:to|com)|vidguard\.to|emturbovid\.com|streamhide\.(?:to|com)|luluvdo\.com|vidmoly\.me)/[a-zA-Z0-9_\-\./]+',
        r'https?://[^\s"\'<>]+\.m3u8(?:\?[^\s"\'<>]*)?',
        r'https?://[^\s"\'<>]+\.mp4(?:\?[^\s"\'<>]*)?'
    ]

    found_streams = []
    for pat in embed_regexes:
        matches = re.findall(pat, page_html, re.IGNORECASE)
        for m in matches:
            if m not in found_streams and not m.endswith('preview.mp4'):
                found_streams.append(m)

    formats = []
    # If embed host links found, attempt extracting via yt-dlp first
    for s_url in found_streams:
        if any(h in s_url for h in ['streamtape', 'dood', 'mixdrop', 'voe', 'filemoon', 'streamwish', 'vidguard']):
            try:
                sub_opts = build_ydl_opts(quality="Best Available (Highest)", output_template=os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s"), proxy=current_proxy)
                sub_opts['extract_flat'] = False
                with yt_dlp.YoutubeDL(sub_opts) as ydl:
                    sub_info = ydl.extract_info(s_url, download=False)
                    if sub_info and sub_info.get('formats'):
                        sub_info['title'] = title or sub_info.get('title')
                        if thumbnail:
                            sub_info['thumbnail'] = thumbnail
                        return sub_info
            except Exception:
                continue

        # If direct m3u8 or mp4
        ext = 'mp4' if '.mp4' in s_url else 'm3u8'
        formats.append({
            'url': s_url,
            'format_id': f"direct-{len(formats)+1}",
            'ext': 'mp4',
            'protocol': 'm3u8_native' if ext == 'm3u8' else 'https',
            'format_note': 'Discovered direct stream'
        })

    if formats:
        return {
            'id': 'discovered_video',
            'title': title,
            'thumbnail': thumbnail,
            'duration': None,
            'uploader': 'Generic Embed Extractor',
            'extractor': 'Universal Embedded Scraper',
            'formats': formats,
        }

    return None

def is_terabox_url(url: str) -> bool:
    """Check if the given URL is a TeraBox, TeleBox, or supported cloud mirror link."""
    u = url.lower()
    terabox_domains = [
        "terabox", "telebox", "1024tera", "4funbox", "mirrobox",
        "nephobox", "freeterabox", "tibibox", "terashare", "terafileshare"
    ]
    return any(d in u for d in terabox_domains) or ("surl=" in u and ("box" in u or "tera" in u))

def extract_terabox_media(url: str, current_proxy: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Multi-tiered TeraBox / TeleBox extractor retrieving title, size, thumbnail, and HLS/direct streams."""
    import urllib.request
    import urllib.parse
    import json
    import re
    import html as html_lib

    # Normalize short code (surl)
    parsed = urllib.parse.urlparse(url)
    surl = None
    if "surl=" in parsed.query:
        qs = urllib.parse.parse_qs(parsed.query)
        surl = qs["surl"][0]
    elif "/s/" in parsed.path:
        surl = parsed.path.split("/s/")[1].split("/")[0].split("?")[0]

    result = {
        "id": surl or "terabox_video",
        "title": "TeraBox Video",
        "thumbnail": None,
        "duration": None,
        "uploader": "TeraBox Cloud Storage",
        "extractor": "TeraBox / TeleBox Pro Extractor",
        "extractor_key": "TeraBox",
        "formats": [],
        "filesize_approx": None,
        "webpage_url": url,
        "is_terabox": True,
        "surl": surl,
    }

    handlers = []
    if current_proxy:
        handlers.append(urllib.request.ProxyHandler({"http": current_proxy, "https": current_proxy}))
    opener = urllib.request.build_opener(*handlers)

    # ── TIER 1: High-Speed Cloud Resolver Gateway (Instant Title, Thumbnail, Duration, 720p Stream) ──
    try:
        req_data = json.dumps({"url": url}).encode("utf-8")
        req = urllib.request.Request(
            "https://teraplayer-xfwi.onrender.com/api/preview",
            data=req_data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Content-Type": "application/json",
                "Origin": "https://www.teraplayer.in",
                "Referer": "https://www.teraplayer.in/",
            }
        )
        with opener.open(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                if data.get("title"):
                    result["title"] = html_lib.unescape(data["title"])
                if data.get("duration"):
                    result["duration"] = int(data["duration"])
                if data.get("thumbnail"):
                    result["thumbnail"] = data["thumbnail"]
                if data.get("size"):
                    result["filesize_approx"] = int(data["size"])
                
                stream_url = data.get("stream_url")
                if stream_url:
                    result["stream_url"] = stream_url
                    result["formats"].append({
                        "url": stream_url,
                        "format_id": "terabox-hls-720p",
                        "ext": "mp4",
                        "format_note": f"HLS Stream ({data.get('resolution', '720p')})",
                        "protocol": "m3u8_native",
                        "http_headers": {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Referer": "https://www.teraplayer.in/",
                            "Origin": "https://www.teraplayer.in",
                        }
                    })
                return result
    except Exception:
        pass

    # ── TIER 2: Native TeraBox CSRF Token & Metadata Extraction ──
    try:
        clean_surl = surl or ""
        wap_url = f"https://www.terabox.app/wap/share/filelist?surl={clean_surl}" if clean_surl else url
        req = urllib.request.Request(
            wap_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
        )
        with opener.open(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            cookies = resp.headers.get_all("Set-Cookie")

        cookie_dict = {}
        if cookies:
            for c in cookies:
                parts = c.split(";")[0].split("=", 1)
                if len(parts) == 2:
                    cookie_dict[parts[0].strip()] = parts[1].strip()
        cookie_hdr = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])

        # Extract jsToken
        token = None
        m_decode = re.search(r"decodeURIComponent\([`\'\"](.*?)[\'\"\`]\)", html)
        if m_decode:
            decoded_js = urllib.parse.unquote(m_decode.group(1))
            m_fn = re.search(r"fn\((\"[a-fA-F0-9]+\")\)", decoded_js)
            if m_fn:
                token = m_fn.group(1).replace('"', '')

        if not token:
            m_direct = re.search(r"fn\((\"[a-fA-F0-9]+\")\)", html)
            if m_direct:
                token = m_direct.group(1).replace('"', '')

        test_surls = [f"1{clean_surl}" if not clean_surl.startswith("1") else clean_surl, clean_surl]
        for s in test_surls:
            if not s:
                continue
            params = {
                "app_id": "250528",
                "web": "1",
                "channel": "dubox",
                "clienttype": "0",
                "jsToken": token or "",
                "shorturl": s,
                "root": "1"
            }
            api_url = "https://www.terabox.app/api/shorturlinfo?" + urllib.parse.urlencode(params)
            req2 = urllib.request.Request(
                api_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": wap_url,
                    "Cookie": cookie_hdr
                }
            )
            with opener.open(req2, timeout=10) as resp2:
                meta = json.loads(resp2.read().decode("utf-8"))
                if meta.get("errno") == 0 and meta.get("list"):
                    f0 = meta["list"][0]
                    result["title"] = f0.get("server_filename") or result["title"]
                    result["filesize_approx"] = int(f0.get("size", 0))
                    thumbs = f0.get("thumbs", {})
                    result["thumbnail"] = thumbs.get("url3") or thumbs.get("url2") or thumbs.get("url1")
                    result["fs_id"] = f0.get("fs_id")
                    result["shareid"] = meta.get("shareid")
                    result["uk"] = meta.get("uk")
                    result["sign"] = meta.get("sign")
                    result["timestamp"] = meta.get("timestamp")

                    # If dlink exists in file metadata
                    if f0.get("dlink"):
                        result["formats"].append({
                            "url": f0["dlink"],
                            "format_id": "terabox-direct",
                            "ext": "mp4",
                            "format_note": "Direct PCS Download Stream",
                            "protocol": "https"
                        })
                    return result
    except Exception:
        pass

    return result if (result.get("formats") or result.get("filesize_approx")) else None

def fetch_media_info_with_failover(url: str, proxy_list: list) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch video metadata with automatic failover across proxy pool, TeraBox resolver, and generic fallback."""
    url_candidates = get_url_candidates(url)
    attempts = proxy_list if proxy_list else [None]
    last_error = None

    # Check if this is a TeraBox or TeleBox link first
    if is_terabox_url(url):
        st.info("📦 Detected TeraBox / TeleBox link! Running Deep TeraBox Media Extractor...")
        for idx, current_proxy in enumerate(attempts):
            proxy_desc = current_proxy.split('@')[-1] if current_proxy and '@' in current_proxy else (current_proxy or "Direct")
            terabox_info = extract_terabox_media(url, current_proxy)
            if terabox_info and (terabox_info.get("formats") or terabox_info.get("filesize_approx")):
                st.success(f"✅ Extracted TeraBox video: **{terabox_info.get('title')}**")
                return terabox_info, current_proxy
            if len(attempts) > 1 and idx < len(attempts) - 1:
                st.warning(f"⚠️ Proxy node `{proxy_desc}` failed for TeraBox... Trying next node...")

    for target_url in url_candidates:
        for idx, current_proxy in enumerate(attempts):
            proxy_desc = current_proxy.split('@')[-1] if current_proxy and '@' in current_proxy else (current_proxy or "Direct")
            opts = build_ydl_opts(
                quality="Best Available (Highest)",
                output_template=os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s"),
                proxy=current_proxy
            )
            opts['extract_flat'] = False
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(target_url, download=False)
                    return info, current_proxy
            except Exception as e:
                last_error = str(e)

                # Check if it is a TeraBox link that wasn't identified earlier
                if is_terabox_url(target_url):
                    st.info("📦 Running fallback TeraBox Cloud Extractor...")
                    tb_info = extract_terabox_media(target_url, current_proxy)
                    if tb_info and (tb_info.get("formats") or tb_info.get("filesize_approx")):
                        st.success(f"✅ Discovered TeraBox stream: **{tb_info.get('title')}**")
                        return tb_info, current_proxy

                # If unsupported URL by yt-dlp, trigger fallback generic embedded scraper
                if "Unsupported URL" in last_error or "generic" in last_error.lower():
                    st.info("🔍 URL not in yt-dlp's default database. Running Universal Embedded Stream Scraper...")
                    fallback_info = fallback_generic_extractor(target_url, current_proxy)
                    if fallback_info:
                        st.success(f"✅ Discovered {len(fallback_info.get('formats', []))} video stream(s) via embedded scraper!")
                        return fallback_info, current_proxy

                if len(attempts) > 1 and idx < len(attempts) - 1:
                    st.warning(f"⚠️ Proxy node `{proxy_desc}` failed: {last_error[:120]}... Trying next node...")
                    continue
                break

    st.error(f"❌ Error fetching metadata: {last_error}")
    
    if "Unsupported URL" in str(last_error):
        st.info("""
        💡 **Unsupported URL Information**:
        This website uses a custom proprietary player script that does not expose public stream links or standard video hosting iframes.
        If the page has embed links (like Streamtape, Doodstream, Mixdrop, or direct `.mp4`/`.m3u8` links), you can paste that specific link directly!
        """)
    return None, None

# ----------------- MAIN UI -----------------

# ── INSTANT ONE-TAP MOBILE / PC RECEIVE BANNER (QR CODE / DIRECT LINK) ──
query_share_code = ""
try:
    if "share" in st.query_params and st.query_params["share"]:
        query_share_code = str(st.query_params["share"]).strip().replace(" ", "").replace("-", "")
except Exception:
    pass

if query_share_code:
    shared_entry = FileShareManager.get_share(query_share_code)
    if shared_entry:
        curr_client_ip = get_effective_host_ip()
        fast_dl_link = f"http://{curr_client_ip}:{STREAM_PORT}/dl/{shared_entry['code']}/{urllib.parse.quote(shared_entry['filename'])}"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1f242d, #14171d); border: 2px solid #ff4b4b; border-radius: 14px; padding: 18px 20px; margin-bottom: 24px; box-shadow: 0 6px 24px rgba(255, 75, 75, 0.3);">
            <div style="color: #ff4b4b; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1.5px;">
                🎉 Incoming Shared File (Key: {shared_entry['code']})
            </div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #ffffff; margin: 6px 0;">
                📄 {shared_entry['filename']}
            </div>
            <div style="color: #bbb; font-size: 0.9rem; margin-bottom: 12px;">
                Size: <b>{format_bytes_human(shared_entry['size'])}</b> &nbsp;|&nbsp; Downloads: <b>{shared_entry['downloads']}</b>
            </div>
            <a href="{fast_dl_link}" download="{shared_entry['filename']}" style="
                display: flex;
                align-items: center;
                justify-content: center;
                width: 100%;
                min-height: 48px;
                padding: 12px 18px;
                font-size: 1.05rem;
                font-weight: 700;
                color: #ffffff !important;
                background: linear-gradient(135deg, #ff4b4b, #d93838);
                border: none;
                border-radius: 8px;
                text-decoration: none !important;
                cursor: pointer;
                text-align: center;
                box-sizing: border-box;
                box-shadow: 0 4px 14px rgba(255, 75, 75, 0.4);
            ">
                💾 One-Tap Instant Download ({format_bytes_human(shared_entry['size'])})
            </a>
        </div>
        """, unsafe_allow_html=True)

tab_single, tab_batch, tab_share, tab_guide = st.tabs([
    "🚀 Single URL Downloader",
    "📑 Batch Downloader",
    "⚡ Send & Receive (5GB Fast Share)",
    "📖 Bypass & Security Guide"
])

# ----------------- TAB 1: SINGLE DOWNLOADER -----------------
with tab_single:
    col_url, col_btn = st.columns([5, 1])
    with col_url:
        video_url = st.text_input(
            "Video URL",
            placeholder="Paste URL here (YouTube,Twitter/X, Instagram, etc.)...",
            label_visibility="collapsed"
        )
    with col_btn:
        inspect_clicked = st.button("🔍 Analyze URL", use_container_width=True)

    if video_url:
        # Check if analyzed info is already cached in session_state for this URL
        if "current_info" not in st.session_state or st.session_state.get("current_url") != video_url:
            if inspect_clicked or st.session_state.get("auto_analyze", True):
                with st.spinner("Analyzing media streams & connecting through proxy pool..."):
                    info, working_proxy = fetch_media_info_with_failover(video_url, active_proxies)
                    if info:
                        st.session_state["current_info"] = info
                        st.session_state["current_url"] = video_url
                        st.session_state["working_proxy"] = working_proxy

        info = st.session_state.get("current_info")
        if info and st.session_state.get("current_url") == video_url:
            title = info.get("title", "Unknown Title")
            duration = info.get("duration", 0)
            thumbnail = info.get("thumbnail")
            uploader = info.get("uploader") or info.get("channel") or "Unknown"
            extractor = info.get("extractor_key") or info.get("extractor", "Generic")
            view_count = info.get("view_count")

            # Display Media Overview Card
            col_thumb, col_details = st.columns([1, 2])
            with col_thumb:
                if thumbnail:
                    st.image(thumbnail, use_container_width=True)
                else:
                    st.info("No thumbnail available")
            with col_details:
                st.subheader(title)
                st.write(f"**Platform / Extractor:** `{extractor}`")
                st.write(f"**Uploader:** {uploader}")
                if duration:
                    mins, secs = divmod(int(duration), 60)
                    hours, mins = divmod(mins, 60)
                    dur_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"
                    st.write(f"**Duration:** ⏱️ {dur_str}")
                if info.get("filesize_approx"):
                    size_mb = info["filesize_approx"] / (1024 * 1024)
                    st.write(f"**Cloud File Size:** 📦 {size_mb:.1f} MB")
                if view_count:
                    st.write(f"**Views:** 👁️ {view_count:,}")

            if info.get("is_terabox") or is_terabox_url(video_url):
                import urllib.parse
                encoded_url = urllib.parse.quote(video_url, safe="")
                st.markdown("#### 🎬 Instant TeraBox Player & Streaming Suite")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.link_button("▶️ Watch in TeraPlayer (HD Stream)", f"https://teraplayer.in/?url={encoded_url}", type="primary", use_container_width=True)
                with col_p2:
                    st.link_button("⚡ Open in Flow Video Player", "https://flowvideoplayer.com", use_container_width=True)
                
                stream_url = info.get("stream_url")
                if stream_url:
                    with st.expander("📺 In-App Video Preview (HLS Player)", expanded=False):
                        _components.html(f"""
                        <div style="width:100%; border-radius:8px; overflow:hidden; background:#000;">
                            <video id="tbVid" controls autoplay playsinline style="width:100%; height:360px;"></video>
                        </div>
                        <script src="https://cdn.jsdelivr.net/npm/hls.js@1.6.16/dist/hls.min.js"></script>
                        <script>
                            var v = document.getElementById('tbVid');
                            var src = '{stream_url}';
                            if (window.Hls && Hls.isSupported()) {{
                                var hls = new Hls();
                                hls.loadSource(src);
                                hls.attachMedia(v);
                            }} else if (v.canPlayType('application/vnd.apple.mpegurl')) {{
                                v.src = src;
                            }}
                        </script>
                        """, height=380)

            st.divider()

            # Resolution & Format Selection
            col_q, col_dbtn = st.columns([2, 1])
            with col_q:
                quality_choice = st.selectbox(
                    "Select Quality / Resolution",
                    [
                        "Best Available (Highest)",
                        "1080p (Full HD)",
                        "720p (HD)",
                        "480p (SD)",
                        "360p",
                        "240p (Low)",
                        "Audio Only (MP3/M4A)"
                    ],
                    index=0
                )
            with col_dbtn:
                st.write("")
                st.write("")
                start_download = st.button("⬇️ Start Download", type="primary", use_container_width=True)

            # Download Execution & Progress Hook
            if start_download:
                progress_bar = st.progress(0)
                status_text = st.empty()
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                metric_speed = metrics_col1.empty()
                metric_size = metrics_col2.empty()
                metric_eta = metrics_col3.empty()

                def progress_hook(d):
                    if d['status'] == 'downloading':
                        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                        downloaded_bytes = d.get('downloaded_bytes', 0)
                        speed = d.get('speed', 0)
                        eta = d.get('eta', 0)

                        if total_bytes > 0:
                            pct = min(1.0, max(0.0, downloaded_bytes / total_bytes))
                            progress_bar.progress(pct)
                            status_text.text(f"Downloading... {int(pct * 100)}%")
                        else:
                            status_text.text("Downloading (stream size dynamic)...")

                        if speed:
                            speed_mb = speed / (1024 * 1024)
                            metric_speed.metric("Speed", f"{speed_mb:.2f} MB/s")
                        if downloaded_bytes:
                            dl_mb = downloaded_bytes / (1024 * 1024)
                            total_mb = (total_bytes / (1024 * 1024)) if total_bytes else 0
                            metric_size.metric("Downloaded", f"{dl_mb:.1f} / {total_mb:.1f} MB" if total_mb else f"{dl_mb:.1f} MB")
                        if eta:
                            metric_eta.metric("ETA", f"{int(eta)}s")
                    elif d['status'] == 'finished':
                        progress_bar.progress(1.0)
                        status_text.text("Download complete! Finalizing & converting format...")

                output_template = os.path.join(DOWNLOADS_DIR, "%(title).100s-%(id)s.%(ext)s")
                
                # Order attempts with known working proxy first
                candidate_proxies = []
                if st.session_state.get("working_proxy"):
                    candidate_proxies.append(st.session_state.get("working_proxy"))
                for p in active_proxies:
                    if p not in candidate_proxies:
                        candidate_proxies.append(p)
                if not candidate_proxies:
                    candidate_proxies = [None]

                download_success = False
                file_path = None
                
                for idx, current_proxy in enumerate(candidate_proxies):
                    p_desc = current_proxy.split('@')[-1] if current_proxy and '@' in current_proxy else (current_proxy or "Direct")
                    status_text.text(f"Connecting to stream via `{p_desc}`...")
                    ydl_opts = build_ydl_opts(
                        quality=quality_choice,
                        output_template=output_template,
                        proxy=current_proxy,
                        progress_hook=progress_hook
                    )

                    try:
                        cached_info = st.session_state.get("current_info")
                        if is_terabox_url(video_url) or (cached_info and cached_info.get("is_terabox")):
                            status_text.text(f"⚡ Downloading TeraBox stream via `{p_desc}`...")
                            tb_data = cached_info if (cached_info and cached_info.get("stream_url")) else extract_terabox_media(video_url, current_proxy)
                            stream_url = tb_data.get("stream_url") if tb_data else None
                            if not stream_url and tb_data and tb_data.get("formats"):
                                stream_url = tb_data["formats"][0].get("url")

                            if not stream_url:
                                raise Exception("Could not retrieve active TeraBox video stream URL. Please try again.")

                            # Set clean filename template without double extensions
                            title_val = tb_data.get("title", "terabox_video")
                            if title_val.lower().endswith(".mp4"):
                                title_val = title_val[:-4]
                            tb_outtmpl = os.path.join(DOWNLOADS_DIR, f"{title_val}.%(ext)s")

                            tb_opts = build_ydl_opts(
                                quality=quality_choice,
                                output_template=tb_outtmpl,
                                proxy=current_proxy,
                                progress_hook=progress_hook,
                                extra_headers={
                                    "Referer": "https://www.teraplayer.in/",
                                    "Origin": "https://www.teraplayer.in"
                                }
                            )
                            tb_opts['format'] = 'best'
                            with yt_dlp.YoutubeDL(tb_opts) as ydl:
                                dl_info = ydl.extract_info(stream_url, download=True)
                                file_path = ydl.prepare_filename(dl_info)
                        else:
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                if cached_info and cached_info.get("extractor") == "Universal Embedded Scraper":
                                    if cached_info.get("formats"):
                                        dl_info = ydl.process_ie_result(cached_info, download=True)
                                    else:
                                        dl_info = ydl.extract_info(cached_info.get("webpage_url", video_url), download=True)
                                elif cached_info and cached_info.get("webpage_url") and cached_info.get("webpage_url") != video_url:
                                    dl_info = ydl.extract_info(cached_info.get("webpage_url"), download=True)
                                else:
                                    dl_info = ydl.extract_info(video_url, download=True)

                                file_path = ydl.prepare_filename(dl_info)
                            
                        # If audio postprocessing happened, ext might be mp3
                        if quality_choice == "Audio Only (MP3/M4A)" and file_path:
                            base, _ = os.path.splitext(file_path)
                            if os.path.exists(base + ".mp3"):
                                file_path = base + ".mp3"

                        # If format merged to mp4
                        if file_path and not os.path.exists(file_path):
                            base, _ = os.path.splitext(file_path)
                            if os.path.exists(base + ".mp4"):
                                file_path = base + ".mp4"

                        download_success = True
                        break
                    except Exception as e:
                        if len(candidate_proxies) > 1 and idx < len(candidate_proxies) - 1:
                            st.warning(f"⚠️ Node `{p_desc}` failed during download: {str(e)[:100]}... Switching to next proxy...")
                            continue
                        else:
                            st.error(f"❌ Download failed: {str(e)}")
                if download_success and file_path and os.path.exists(file_path):
                    # Automatic WhatsApp & Mobile Compatibility Pass
                    # Remuxes into clean ISO MP4 (+faststart) and strips non-standard metadata streams (e.g. timed_id3)
                    if file_path.endswith(".mp4"):
                        try:
                            temp_fs = file_path + ".tmp.mp4"
                            r = subprocess.run([
                                "ffmpeg", "-y", "-v", "error", "-i", file_path,
                                "-c", "copy", "-map", "0:v", "-map", "0:a?",
                                "-movflags", "+faststart", temp_fs
                            ], capture_output=True, timeout=30)
                            if r.returncode == 0 and os.path.exists(temp_fs) and os.path.getsize(temp_fs) > 1000:
                                os.replace(temp_fs, file_path)
                        except Exception:
                            pass

                    st.success(f"🎉 Processing complete! Your video is ready.")
                    
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    st.caption(f"📦 File: `{os.path.basename(file_path)}` ({file_size_mb:.1f} MB)")

                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                    
                    st.download_button(
                        label="📱 💾 Tap to Save Video to Your Phone / Device",
                        data=file_bytes,
                        file_name=os.path.basename(file_path),
                        mime="video/mp4" if not file_path.endswith(".mp3") else "audio/mp3",
                        use_container_width=True,
                        type="primary"
                    )

# ----------------- TAB 2: BATCH DOWNLOADER -----------------
with tab_batch:
    st.subheader("📑 Batch Video Downloader")
    st.caption("Paste multiple video URLs (one per line) to download in batch.")
    
    batch_urls = st.text_area("URLs (One per line)", height=150, placeholder="https://...\nhttps://...\nhttps://...")
    batch_quality = st.selectbox(
        "Batch Quality",
        ["Best Available (Highest)", "1080p (Full HD)", "720p (HD)", "480p (SD)", "Audio Only (MP3/M4A)"],
        key="batch_q"
    )
    
    if st.button("🚀 Start Batch Download", type="primary"):
        urls = [u.strip() for u in batch_urls.strip().splitlines() if u.strip()]
        if not urls:
            st.warning("Please provide at least one valid URL.")
        else:
            st.write(f"Found {len(urls)} URLs. Starting downloads...")
            overall_progress = st.progress(0)
            
            for idx, url in enumerate(urls):
                st.write(f"**[{idx+1}/{len(urls)}] Processing:** `{url}`")
                batch_status = st.empty()
                output_tmpl = os.path.join(DOWNLOADS_DIR, "%(title).100s-%(id)s.%(ext)s")
                
                batch_candidates = active_proxies if active_proxies else [None]
                batch_done = False
                last_batch_err = ""
                
                for b_proxy in batch_candidates:
                    opts = build_ydl_opts(quality=batch_quality, output_template=output_tmpl, proxy=b_proxy)
                    try:
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            if is_terabox_url(url):
                                tb_meta = extract_terabox_media(url, b_proxy)
                                stream_url = tb_meta.get("stream_url") if tb_meta else None
                                if not stream_url and tb_meta and tb_meta.get("formats"):
                                    stream_url = tb_meta["formats"][0].get("url")
                                if stream_url:
                                    tb_title = (tb_meta.get("title") or "terabox_video").rstrip(".mp4")
                                    tb_batch_opts = build_ydl_opts(
                                        quality=batch_quality,
                                        output_template=os.path.join(DOWNLOADS_DIR, f"{tb_title}.%(ext)s"),
                                        proxy=b_proxy,
                                        extra_headers={
                                            "Referer": "https://www.teraplayer.in/",
                                            "Origin": "https://www.teraplayer.in"
                                        }
                                    )
                                    tb_batch_opts['format'] = 'best'
                                    with yt_dlp.YoutubeDL(tb_batch_opts) as tb_ydl:
                                        tb_ydl.extract_info(stream_url, download=True)
                                else:
                                    raise Exception("Failed to resolve TeraBox video stream.")
                            else:
                                ydl.extract_info(url, download=True)
                        batch_status.success("✅ Complete")
                        batch_done = True
                        break
                    except Exception as err:
                        last_batch_err = str(err)
                        continue
                
                if not batch_done:
                    batch_status.error(f"❌ Failed across proxies: {last_batch_err}")
                
                overall_progress.progress((idx + 1) / len(urls))
            
            st.success("🎉 Batch processing finished! Files saved in `downloads/` directory.")

# ----------------- TAB 3: 5GB FAST FILE & CODE SHARING -----------------
with tab_share:
    st.subheader("⚡ Send & Receive: Fast 5GB File, Video & Code Sharing")
    st.caption("Transfer files up to 5 GB, share downloaded videos instantly, or copy/paste code snippets between laptops and mobile phones in seconds using a 6-digit code or QR.")

    share_tab_send, share_tab_recv, share_tab_manage = st.tabs([
        "📤 Send (File, Video or Text)",
        "📥 Receive (Enter 6-Digit Code)",
        "📋 Active Transfers & Storage"
    ])

    # ── SUB-TAB 1: SEND ──
    with share_tab_send:
        send_type = st.radio(
            "What would you like to share?",
            [
                "📱 Upload File from Phone or Laptop (Photos, Videos, Files)",
                "💻 Share Local File on Laptop (Zero RAM, Instant, Up to 50 GB)",
                "📝 Quick Paste Text / Code / Clipboard"
            ],
            horizontal=True
        )

        col_cfg1, col_cfg2 = st.columns([2, 2])
        with col_cfg1:
            expiry_choice = st.selectbox(
                "Link Expiry Time",
                ["10 Minutes", "30 Minutes", "1 Hour (Recommended)", "6 Hours", "24 Hours"],
                index=2
            )
            expiry_map = {
                "10 Minutes": 600,
                "30 Minutes": 1800,
                "1 Hour (Recommended)": 3600,
                "6 Hours": 21600,
                "24 Hours": 86400
            }
            expiry_sec = expiry_map[expiry_choice]

        with col_cfg2:
            one_time_dl = st.checkbox("🗑️ Burn after reading (Delete automatically after 1st download)", value=False)

        generated_share = None

        if send_type == "📱 Upload File from Phone or Laptop (Photos, Videos, Files)":
            st.info("⚡ **Fast 5GB Chunked Uploader**: Upload any file, video, or photo (up to 5 GB) with live progress, real-time speed, and zero RAM limits!")

            client_ip = get_effective_host_ip()
            upload_target_port = STREAM_PORT

            import streamlit.components.v1 as _components
            uploader_component = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
                body {{ margin: 0; padding: 8px; background: transparent; color: #fff; }}
                .drop-area {{
                    border: 2px dashed #ff4b4b;
                    border-radius: 12px;
                    padding: 26px 16px;
                    text-align: center;
                    background: rgba(255, 75, 75, 0.05);
                    cursor: pointer;
                    transition: all 0.2s ease;
                }}
                .drop-area:hover, .drop-area.active {{
                    background: rgba(255, 75, 75, 0.12);
                    border-color: #ff2b2b;
                }}
                .icon {{ font-size: 2.4rem; margin-bottom: 6px; }}
                .title {{ font-size: 1.1rem; font-weight: 700; color: #fff; margin-bottom: 4px; }}
                .subtitle {{ font-size: 0.85rem; color: #aaa; margin-bottom: 14px; }}
                .upload-btn {{
                    display: inline-block;
                    background: linear-gradient(135deg, #ff4b4b, #d93838);
                    color: #fff;
                    border: none;
                    padding: 10px 24px;
                    border-radius: 8px;
                    font-size: 0.95rem;
                    font-weight: 700;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(255, 75, 75, 0.35);
                }}
                .progress-box {{
                    display: none;
                    margin-top: 14px;
                    background: #191c22;
                    border: 1px solid #2d3139;
                    border-radius: 10px;
                    padding: 18px 16px;
                }}
                .progress-bar-wrap {{
                    background: #2D3139;
                    border-radius: 6px;
                    height: 14px;
                    overflow: hidden;
                    margin: 10px 0;
                }}
                .progress-bar-fill {{
                    background: linear-gradient(90deg, #ff4b4b, #ff7b7b);
                    height: 100%;
                    width: 0%;
                    transition: width 0.1s linear;
                }}
                .stats-row {{
                    display: flex;
                    justify-content: space-between;
                    font-size: 0.85rem;
                    color: #bbb;
                    flex-wrap: wrap;
                    gap: 6px;
                }}
                .result-box {{
                    display: none;
                    background: linear-gradient(145deg, #1A1D24, #13151A);
                    border: 2px solid #ff4b4b;
                    border-radius: 12px;
                    padding: 20px 16px;
                    text-align: center;
                    margin-top: 14px;
                    box-shadow: 0 6px 20px rgba(0,0,0,0.4);
                }}
                .pin-title {{
                    font-size: 0.85rem;
                    color: #888;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                }}
                .pin-val {{
                    font-size: 2.8rem;
                    font-weight: 800;
                    letter-spacing: 8px;
                    color: #ff4b4b;
                    font-family: monospace;
                    margin: 8px 0;
                    text-shadow: 0 0 15px rgba(255, 75, 75, 0.4);
                }}
                .qr-img {{
                    max-width: 170px;
                    border-radius: 8px;
                    margin: 10px auto;
                    display: block;
                    background: #fff;
                    padding: 4px;
                }}
                .link-btn {{
                    display: inline-block;
                    margin: 4px;
                    padding: 8px 16px;
                    background: #2D3139;
                    color: #fff;
                    border-radius: 6px;
                    border: none;
                    text-decoration: none;
                    font-size: 0.85rem;
                    cursor: pointer;
                }}
                .err-box {{
                    background: #2a1515;
                    border: 1px solid #ff4b4b;
                    border-radius: 8px;
                    padding: 12px;
                    color: #ff8080;
                    margin-top: 12px;
                    font-size: 0.88rem;
                    display: none;
                }}
            </style>
            </head>
            <body>
            <div id="dropZone" class="drop-area" onclick="document.getElementById('fInput').click()">
                <div class="icon">🚀</div>
                <div class="title">Select or Drag &amp; Drop File (Up to 5 GB)</div>
                <div class="subtitle">On Phone: opens Camera, Gallery, or Files &nbsp;|&nbsp; On PC: drag any file here</div>
                <button type="button" class="upload-btn">📁 Browse / Choose File</button>
                <input type="file" id="fInput" style="display:none;" onchange="handleFileSelected(this.files)">
            </div>

            <div id="progBox" class="progress-box">
                <div id="fnameDisplay" style="font-weight:700; font-size:1rem; margin-bottom:6px; color:#fff;"></div>
                <div class="progress-bar-wrap">
                    <div id="progFill" class="progress-bar-fill"></div>
                </div>
                <div class="stats-row">
                    <span id="transferredText">0 B / 0 B (0%)</span>
                    <span id="speedText">Connecting...</span>
                    <span id="etaText">Estimating...</span>
                </div>
                <div id="indBar" style="display:none; margin-top:8px; font-size:0.8rem; color:#888;">⏳ Uploading — please wait, do not close this page...</div>
            </div>

            <div id="errBox" class="err-box"></div>

            <div id="resBox" class="result-box">
                <div class="pin-title">🎉 Upload Complete! 6-Digit Transfer Key:</div>
                <div id="pinDisplay" class="pin-val">000 000</div>
                <div style="font-size:0.9rem; color:#bbb; margin-bottom:10px;">
                    Enter this key in the <b>Receive</b> tab on another phone or laptop!
                </div>
                <img id="qrImg" class="qr-img" src="" alt="QR Code">
                <div>
                    <button class="link-btn" onclick="copyShareLink()">📋 Copy One-Tap Link</button>
                    <button class="link-btn" style="background:#ff4b4b; color:#fff;" onclick="window.parent.location.reload()">🔄 Done / Upload Another</button>
                </div>
            </div>

            <script>
                var shareUrl = "";
                var uploadedBytes = 0;
                var totalSize = 0;
                var startTime = 0;

                function formatBytes(bytes) {{
                    if (!bytes || bytes <= 0) return '0 B';
                    var k = 1024;
                    var sizes = ['B', 'KB', 'MB', 'GB'];
                    var i = Math.floor(Math.log(bytes) / Math.log(k));
                    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
                }}

                function showError(msg) {{
                    var eb = document.getElementById('errBox');
                    eb.style.display = 'block';
                    eb.innerText = '❌ ' + msg;
                    document.getElementById('dropZone').style.display = 'block';
                    document.getElementById('progBox').style.display = 'none';
                }}

                function handleFileSelected(files) {{
                    if (!files || files.length === 0) return;
                    startUpload(files[0]);
                }}

                var dropArea = document.getElementById('dropZone');
                ['dragenter', 'dragover'].forEach(function(name) {{
                    dropArea.addEventListener(name, function(e) {{ e.preventDefault(); e.stopPropagation(); dropArea.classList.add('active'); }}, false);
                }});
                ['dragleave', 'drop'].forEach(function(name) {{
                    dropArea.addEventListener(name, function(e) {{ e.preventDefault(); e.stopPropagation(); dropArea.classList.remove('active'); }}, false);
                }});
                dropArea.addEventListener('drop', function(e) {{
                    handleFileSelected(e.dataTransfer.files);
                }}, false);

                function updateProgress(loaded, total) {{
                    var progFill = document.getElementById('progFill');
                    var transferredText = document.getElementById('transferredText');
                    var speedText = document.getElementById('speedText');
                    var etaText = document.getElementById('etaText');

                    var elapsed = Math.max(0.1, (Date.now() - startTime) / 1000);
                    var bytesPerSec = loaded / elapsed;

                    if (total > 0) {{
                        var pct = Math.min(100, (loaded / total) * 100);
                        progFill.style.width = pct.toFixed(1) + '%';
                        transferredText.innerText = formatBytes(loaded) + ' / ' + formatBytes(total) + ' (' + pct.toFixed(1) + '%)';
                        var rem = total - loaded;
                        var eta = Math.round(rem / Math.max(1, bytesPerSec));
                        etaText.innerText = 'ETA: ' + (eta < 60 ? eta + 's' : Math.round(eta/60) + 'm');
                    }} else {{
                        progFill.style.width = '50%';
                        transferredText.innerText = formatBytes(loaded) + ' uploaded';
                        etaText.innerText = 'Please wait...';
                    }}
                    speedText.innerText = formatBytes(bytesPerSec) + '/s';
                }}

                function startUpload(file) {{
                    document.getElementById('errBox').style.display = 'none';
                    document.getElementById('dropZone').style.display = 'none';
                    var progBox = document.getElementById('progBox');
                    progBox.style.display = 'block';
                    document.getElementById('fnameDisplay').innerText = '📤 Uploading: ' + file.name + ' (' + formatBytes(file.size) + ')';

                    totalSize = file.size;
                    startTime = Date.now();
                    uploadedBytes = 0;

                    var host = window.location.hostname || '{client_ip}';
                    var uploadUrl = 'http://' + host + ':{upload_target_port}/upload?filename=' + encodeURIComponent(file.name);

                    // ── Use XMLHttpRequest with progress tracking ──
                    // Fetch API does not support upload progress on all mobile browsers.
                    var xhr = new XMLHttpRequest();

                    xhr.upload.onprogress = function(e) {{
                        uploadedBytes = e.loaded;
                        updateProgress(e.loaded, e.lengthComputable ? e.total : totalSize);
                    }};

                    xhr.onreadystatechange = function() {{
                        if (xhr.readyState === 4) {{
                            if (xhr.status >= 200 && xhr.status < 300) {{
                                try {{
                                    var resp = JSON.parse(xhr.responseText);
                                    showSuccess(resp, host);
                                }} catch(err) {{
                                    showError('Upload done but response invalid: ' + err + ' | Raw: ' + xhr.responseText.slice(0, 200));
                                }}
                            }} else {{
                                showError('Server error HTTP ' + xhr.status + ': ' + (xhr.responseText || xhr.statusText).slice(0, 300));
                            }}
                        }}
                    }};

                    xhr.onerror = function() {{
                        showError('Network error — could not reach upload server at ' + uploadUrl + '. Make sure you are on the same Wi-Fi network as the PC running this app.');
                    }};

                    xhr.ontimeout = function() {{
                        showError('Connection timed out. For very large files (>1 GB) please ensure a stable Wi-Fi connection.');
                    }};

                    // No timeout for large files — let it run until done
                    xhr.timeout = 0;

                    xhr.open('POST', uploadUrl, true);
                    // NOTE: Do NOT manually set Content-Length — the browser sets it correctly.
                    // Setting it manually can cause issues on some mobile browsers.
                    xhr.send(file);

                    // Animate indeterminate bar if no progress events fire within 3s
                    var indTimer = setTimeout(function() {{
                        if (uploadedBytes === 0) {{
                            document.getElementById('indBar').style.display = 'block';
                        }}
                    }}, 3000);
                }}

                function showSuccess(resp, host) {{
                    document.getElementById('progBox').style.display = 'none';
                    var resBox = document.getElementById('resBox');
                    resBox.style.display = 'block';

                    var code = resp.code;
                    var formatted = code.slice(0, 3) + ' ' + code.slice(3);
                    document.getElementById('pinDisplay').innerText = formatted;

                    shareUrl = 'http://' + host + ':8501/?share=' + code;
                    document.getElementById('qrImg').src =
                        'https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=' + encodeURIComponent(shareUrl);
                }}

                function copyShareLink() {{
                    if (navigator.clipboard && shareUrl) {{
                        navigator.clipboard.writeText(shareUrl).then(function() {{
                            alert('Copied: ' + shareUrl);
                        }}).catch(function() {{ prompt('Copy this link:', shareUrl); }});
                    }} else if (shareUrl) {{
                        prompt('Copy this link:', shareUrl);
                    }}
                }}
            </script>
            </body>
            </html>
            """
            _components.html(uploader_component, height=420, scrolling=False)

        elif send_type == "💻 Share Local File on Laptop (Zero RAM, Instant, Up to 50 GB)":
            st.info("⚡ **Zero-RAM Instant Share**: Share any file on your computer (videos, large ISOs, zips, datasets up to 50 GB) with 0 seconds wait time and 0 MB RAM usage!")
            
            local_src = st.radio(
                "Select Source:",
                ["🎬 App Downloads Folder", "📂 Enter / Paste Any File Path on PC"],
                horizontal=True
            )

            chosen_path = None
            chosen_name = None

            if local_src == "🎬 App Downloads Folder":
                existing_videos = [
                    f for f in os.listdir(DOWNLOADS_DIR)
                    if os.path.isfile(os.path.join(DOWNLOADS_DIR, f))
                ] if os.path.exists(DOWNLOADS_DIR) else []

                if not existing_videos:
                    st.warning("⚠️ No downloaded files found in the `downloads/` folder yet. You can download from Tab 1 or paste a file path below!")
                else:
                    video_options = {}
                    for f in existing_videos:
                        sz = os.path.getsize(os.path.join(DOWNLOADS_DIR, f))
                        video_options[f"{f} ({format_bytes_human(sz)})"] = (os.path.join(DOWNLOADS_DIR, f), f)

                    selected_label = st.selectbox("Select File / Video", list(video_options.keys()))
                    if selected_label:
                        chosen_path, chosen_name = video_options[selected_label]
            else:
                user_input_path = st.text_input(
                    "Paste full file path on your computer",
                    placeholder=r"e.g. D:\Movies\video.mp4 or C:\Users\Smit\Downloads\large_file.zip"
                )
                if user_input_path.strip():
                    cleaned_p = user_input_path.strip().strip('"').strip("'")
                    if os.path.isfile(cleaned_p):
                        chosen_path = cleaned_p
                        chosen_name = os.path.basename(cleaned_p)
                        st.success(f"✅ Found: **{chosen_name}** ({format_bytes_human(os.path.getsize(cleaned_p))})")
                    else:
                        st.error(f"❌ File not found at `{cleaned_p}`. Please verify the path.")

            if chosen_path and chosen_name:
                if st.button("🚀 Generate 6-Digit Code (Instant Zero-RAM Share)", type="primary", use_container_width=True):
                    generated_share = FileShareManager.create_share(
                        filepath=chosen_path,
                        filename=chosen_name,
                        expiry_seconds=expiry_sec,
                        one_time=one_time_dl,
                        delete_on_expiry=False
                    )
                    st.success("🎉 Share key generated instantly!")

        elif send_type == "📝 Quick Paste Text / Code / Clipboard":
            pasted_title = st.text_input("Title / Note (optional)", placeholder="e.g. Secret Credentials, Python Script, Config")
            pasted_text = st.text_area("Paste Text, Code, or Links here", height=180, placeholder="Paste whatever text or code you want to share...")

            if st.button("🚀 Generate 6-Digit Code for Text/Code", type="primary", use_container_width=True):
                if not pasted_text.strip():
                    st.warning("Please paste some text or code first.")
                else:
                    txt_code = FileShareManager.generate_unique_code()
                    txt_path = os.path.join(SHARED_DIR, f"text_{txt_code}.txt")
                    with open(txt_path, "w", encoding="utf-8") as tf:
                        tf.write(pasted_text)

                    generated_share = FileShareManager.create_share(
                        filepath=txt_path,
                        filename=(pasted_title.strip() + ".txt") if pasted_title.strip() else "shared_snippet.txt",
                        expiry_seconds=expiry_sec,
                        one_time=one_time_dl,
                        delete_on_expiry=True,
                        text_content=pasted_text
                    )
                    st.success("🎉 Text/Code snippet ready!")

        # ── SHOW GENERATED SHARE CARD ──
        if generated_share:
            code_str = generated_share["code"]
            formatted_code = f"{code_str[:3]} {code_str[3:]}"
            active_host = get_effective_host_ip()
            direct_share_link = f"http://{active_host}:8501/?share={code_str}"
            direct_stream_url = f"http://{active_host}:{STREAM_PORT}/dl/{code_str}/{urllib.parse.quote(generated_share['filename'])}"

            st.markdown(f"""
            <div class="share-pin-box">
                <div style="font-size: 0.9rem; color: #888; text-transform: uppercase; letter-spacing: 2px;">Your 6-Digit Transfer Key</div>
                <div class="share-pin-code">{formatted_code}</div>
                <div style="font-size: 0.95rem; color: #BBB;">Tell the receiver to enter this code in the <b>Receive</b> tab!</div>
            </div>
            """, unsafe_allow_html=True)

            col_qr, col_info = st.columns([1, 2])
            with col_qr:
                qr_bytes = generate_qr_code_image_bytes(direct_share_link)
                st.image(qr_bytes, caption="📱 Scan with Phone Camera to Receive", use_container_width=True)

            with col_info:
                st.markdown(f"**📦 File:** `{generated_share['filename']}`")
                st.markdown(f"**📊 Size:** `{format_bytes_human(generated_share['size'])}`")
                mins_left = max(1, int((generated_share['expires_at'] - time.time()) / 60))
                st.markdown(f"**⏱️ Expires in:** `{mins_left} minutes`" + (" (Burn after 1st download)" if generated_share['one_time'] else ""))
                
                st.markdown("**🔗 One-Tap Web Link:**")
                st.code(direct_share_link, language="text")

                if generated_share['type'] == 'file':
                    st.markdown("**⚡ Resumable Direct Stream URL (IDM / Mobile Browser):**")
                    st.code(direct_stream_url, language="text")

    # ── SUB-TAB 2: RECEIVE ──
    with share_tab_recv:
        st.markdown("### 📥 Receive File or Code")
        st.caption("Enter the 6-digit key from the sender or scan their QR code to receive the file instantly.")

        # Check if URL parameter pre-fills the code
        default_recv_code = ""
        try:
            if "share" in st.query_params:
                default_recv_code = str(st.query_params["share"]).strip()
        except Exception:
            pass

        col_code_in, col_code_go = st.columns([3, 1])
        with col_code_in:
            recv_code_input = st.text_input(
                "6-Digit Sharing Code",
                value=default_recv_code,
                placeholder="e.g. 582 914",
                label_visibility="collapsed"
            )
        with col_code_go:
            fetch_clicked = st.button("🔍 Get File / Code", type="primary", use_container_width=True)

        target_code = recv_code_input.strip().replace(" ", "").replace("-", "")

        if target_code:
            entry = FileShareManager.get_share(target_code)
            if entry:
                st.success("✅ File found and ready for transfer!")

                st.markdown(f"""
                <div class="share-file-card">
                    <h3 style="margin:0 0 8px 0;">📄 {entry['filename']}</h3>
                    <p style="margin:0; color:#AAA;">
                        <b>Size:</b> {format_bytes_human(entry['size'])} &nbsp;|&nbsp; 
                        <b>Downloads:</b> {entry['downloads']} &nbsp;|&nbsp; 
                        <b>Type:</b> {entry['type'].upper()}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if entry.get("type") == "text" and entry.get("text_content"):
                    st.markdown("#### 📝 Shared Content:")
                    st.code(entry["text_content"], language="text")
                else:
                    filepath = entry.get("filepath")
                    if filepath and os.path.exists(filepath):
                        active_host = get_effective_host_ip()
                        fast_url = f"http://{active_host}:{STREAM_PORT}/dl/{entry['code']}/{urllib.parse.quote(entry['filename'])}"

                        # Single unified download button — works for ALL file sizes (small to 50GB)
                        # HTML5 anchor → streaming server → zero RAM, no size restriction message
                        st.markdown(f"""
                        <a href="{fast_url}" download="{entry['filename']}" style="
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            width: 100%;
                            min-height: 52px;
                            padding: 14px 20px;
                            font-size: 1.05rem;
                            font-weight: 700;
                            color: #ffffff !important;
                            background: linear-gradient(135deg, #ff4b4b, #d93838);
                            border: none;
                            border-radius: 10px;
                            text-decoration: none !important;
                            cursor: pointer;
                            text-align: center;
                            box-sizing: border-box;
                            box-shadow: 0 4px 16px rgba(255, 75, 75, 0.4);
                            transition: all 0.2s ease;
                            margin-bottom: 8px;
                        ">
                            💾 Download — {entry['filename']} ({format_bytes_human(entry['size'])})
                        </a>
                        <div style="text-align:center; margin-top:4px;">
                            <a href="{fast_url}" style="color:#888; font-size:0.78rem; text-decoration:none;">
                                🔗 Direct stream link (IDM / curl / external download managers)
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("❌ File not found on disk. It may have expired or been deleted.")
            elif fetch_clicked or target_code:
                st.error("❌ Invalid or expired 6-digit key. Please check the code and try again.")

    # ── SUB-TAB 3: ACTIVE TRANSFERS & STORAGE ──
    with share_tab_manage:
        st.markdown("### 📋 Active Transfers & Storage Manager")
        active_list = FileShareManager.get_all_active()

        col_m1, col_m2 = st.columns([3, 1])
        with col_m1:
            total_shared_size = sum(x.get("size", 0) for x in active_list)
            st.write(f"Currently **{len(active_list)}** active shared items occupying **{format_bytes_human(total_shared_size)}**.")
        with col_m2:
            if st.button("🧹 Clean Expired Files", use_container_width=True):
                FileShareManager.cleanup_expired_shares()
                st.success("Cleaned!")
                st.rerun()

        if active_list:
            for it in active_list:
                with st.expander(f"📄 {it['filename']} — Key: `{it['code']}` ({format_bytes_human(it['size'])})"):
                    mins_rem = max(0, int((it['expires_at'] - time.time()) / 60))
                    st.write(f"**Expires in:** {mins_rem} minutes | **Downloads:** {it['downloads']} | **One-time:** {it['one_time']}")
                    if st.button(f"🗑️ Revoke / Delete Key {it['code']}", key=f"del_{it['code']}"):
                        FileShareManager.delete_share(it['code'])
                        st.success(f"Revoked {it['code']}")
                        st.rerun()
        else:
            st.caption("No active shared files at the moment.")

# ----------------- TAB 4: BYPASS GUIDE -----------------
with tab_guide:
    st.markdown("""
    ### 🛡️ Website Protection & Bypass Guide

    Modern video platforms (YouTube, adult websites like Pornhub/XHamster/Eporner, and generic video hosts) employ various anti-scraping and access verification mechanisms:

    #### 1. Cloudflare / Bot Challenges & Age Verification
    - **Problem**: Some websites present a Cloudflare challenge ("Just a moment...") or require 18+ age verification consent before serving video streams.
    - **Solution**: Use the **Cookie & Session Bypass** in the sidebar.
      - Install the Chrome extension *Get cookies.txt LOCALLY* or *EditThisCookie*.
      - Visit the website in your browser and pass the verification/age prompt.
      - Export cookies in Netscape format (`cookies.txt`) and upload it in the sidebar.

    #### 2. User-Agent & Header Filtering
    - **Problem**: Sites block python default User-Agents (like `python-requests` or generic headers).
    - **Solution**: The app automatically spoof modern Chrome 125 desktop headers. You can customize the `Referer` or `User-Agent` in the sidebar.

    #### 3. Geo-Restrictions, Blocked Sites & SSTP VPN (Mobile & Laptop)
    - **Problem**: Certain videos/domains are restricted by ISPs, colleges, or geo-locations.
    - **Solution**: Use the **🔒 SSTP VPN Gateway (Mobile & Laptop)** in the sidebar:
      - **Mobile & Laptop One-Tap Gateway**: Tap "Connect SSTP VPN" from any phone or laptop. All downloads initiated from your mobile phone or laptop will automatically be processed through the encrypted SSTP tunnel (Port 443, username: `vpn`, password: `vpn`).
      - **Direct Mobile Phone Connection**: Android and iOS devices can connect directly to OpenGW SSTP (`public-vpn-202.opengw.net:443`, user: `vpn`, pass: `vpn`) using the free *SSTP VPN Client* or *OpenVPN Connect* apps.
      - **Auto-Failover Relay Pool**: Automatically routes stream requests through OpenGW SSTP relay nodes (`public-vpn-202`, `public-vpn-200`, etc.) using `vpn:vpn`.

    #### 4. High-Quality Video + Audio Merging (1080p+)
    - Platforms like YouTube deliver video and audio in separate streams for 1080p, 2K, and 4K resolutions.
    - `yt-dlp` automatically downloads both streams and merges them using `ffmpeg` into a single `.mp4` file.
    """)
