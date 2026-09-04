"""
Universal Video Downloader & Media Extractor (Streamlit + yt-dlp)
Supports 1000+ platforms (YouTube, adult websites, social media, generic hosts)
Includes security bypass options: User-Agent spoofing, cookies injection, proxy, and custom headers.
"""

import os
import sys
import time
import tempfile
import threading
from typing import Dict, Any, Optional
import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="Universal Video Downloader Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS + JS to hide viewer badge profile icon
st.markdown("""
<style>
    /* Hide Streamlit header, menu, footer */
    #MainMenu {visibility: hidden; display: none !important;}
    header {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}

    /* ── VIEWER BADGE (GitHub profile icon bottom-right) ── */
    /* Old class names */
    .viewerBadge_container__1QSob,
    .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK,
    .styles_viewerBadge__1yB5_,
    /* New emotion-cache names - wildcard */
    div[class*="viewerBadge"],
    span[class*="viewerBadge"],
    a[class*="viewerBadge"],
    /* data-testid selectors */
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
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
    }

    /* Hide any fixed-position anchor that links to github.com or share.streamlit.io/user */
    a[href*="github.com"],
    a[href*="share.streamlit.io/user"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Adjust top padding since header is hidden */
    .block-container {
        padding-top: 1.5rem !important;
    }

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
</style>
""", unsafe_allow_html=True)

# ── HIDE VIEWER BADGE via iframe JS (only way to run real JS in Streamlit) ──
import streamlit.components.v1 as _components
_components.html("""
<script>
(function() {
    function hideViewerBadge() {
        try {
            var doc = window.parent.document;
            // 1. Target by class wildcard (viewerBadge in class name)
            doc.querySelectorAll('[class*="viewerBadge"]').forEach(function(el) {
                el.style.setProperty('display', 'none', 'important');
                if (el.parentElement) {
                    el.parentElement.style.setProperty('display', 'none', 'important');
                }
            });
            // 2. Target the anchor links that go to github profile or streamlit user profile
            doc.querySelectorAll('a').forEach(function(a) {
                var href = a.getAttribute('href') || '';
                if (href.indexOf('github.com') !== -1 || href.indexOf('share.streamlit.io/user') !== -1) {
                    a.style.setProperty('display', 'none', 'important');
                    var p = a.parentElement;
                    if (p) p.style.setProperty('display', 'none', 'important');
                    var pp = p && p.parentElement;
                    if (pp) pp.style.setProperty('display', 'none', 'important');
                }
            });
            // 3. Target img elements that are circular badges (small size, avatar-like)
            doc.querySelectorAll('img').forEach(function(img) {
                var src = img.getAttribute('src') || '';
                if (src.indexOf('githubusercontent.com') !== -1 || src.indexOf('avatars') !== -1) {
                    var p = img.closest('a') || img.parentElement;
                    if (p) p.style.setProperty('display', 'none', 'important');
                }
            });
        } catch(e) {}
    }

    // Run immediately and repeatedly
    hideViewerBadge();
    [200, 500, 1000, 1500, 2000, 3000, 5000].forEach(function(t) {
        setTimeout(hideViewerBadge, t);
    });

    // Watch for DOM changes and hide badge when it appears
    try {
        var observer = new MutationObserver(function() { hideViewerBadge(); });
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

# OpenGW / VPNGate Public Relay Node Pool
OPENGW_SERVERS = [
    "public-vpn-200.opengw.net",
    "public-vpn-159.opengw.net",
    "vpn801875041.opengw.net",
    "public-vpn-230.opengw.net",
    "opengw.opengw.net",
    "vpn650277207.opengw.net",
    "vpn864131273.opengw.net",
]

with st.sidebar.expander("🔒 Proxy & VPN Gateway (Auto-Failover)", expanded=True):
    proxy_mode = st.selectbox(
        "Proxy / VPN Mode",
        [
            "None (Direct Connection)",
            "Auto-Failover OpenGW Pool (Recommended for Blocked Sites)",
            "Specific OpenGW Server",
            "Custom Proxy URL"
        ],
        index=0
    )

    proxy_protocol = "http"
    proxy_port = "8080"
    active_proxies = []

    if proxy_mode == "Auto-Failover OpenGW Pool (Recommended for Blocked Sites)":
        st.info("🔄 Will try `public-vpn-200` first. If it fails, automatically falls back through 6 other OpenGW servers (user: `vpn`, pass: `vpn`).")
        col_prot, col_pt = st.columns(2)
        with col_prot:
            proxy_protocol = st.selectbox("Protocol", ["http", "socks5", "https"], index=0)
        with col_pt:
            proxy_port = st.text_input("Port", value="8080")

        # Generate list of proxy strings in failover order
        for srv in OPENGW_SERVERS:
            active_proxies.append(f"{proxy_protocol}://vpn:vpn@{srv}:{proxy_port}")

    elif proxy_mode == "Specific OpenGW Server":
        selected_srv = st.selectbox("Select OpenGW Server", OPENGW_SERVERS)
        col_prot, col_pt = st.columns(2)
        with col_prot:
            proxy_protocol = st.selectbox("Protocol", ["http", "socks5", "https"], index=0)
        with col_pt:
            proxy_port = st.text_input("Port", value="8080")
        active_proxies.append(f"{proxy_protocol}://vpn:vpn@{selected_srv}:{proxy_port}")
        st.caption(f"Configured: `{proxy_protocol}://vpn:vpn@{selected_srv}:{proxy_port}`")

    elif proxy_mode == "Custom Proxy URL":
        custom_p = st.text_input("Proxy URL", placeholder="http://user:pass@host:port or socks5://host:port")
        if custom_p.strip():
            active_proxies.append(custom_p.strip())

    socket_timeout = st.slider("Socket Timeout (seconds)", min_value=5, max_value=60, value=20)
    retries = st.slider("Max Connection Retries", min_value=1, max_value=20, value=5)
    fragment_retries = st.slider("HLS/DASH Fragment Retries", min_value=1, max_value=30, value=15)
    rate_limit = st.text_input("Rate Limit (optional, e.g. 5M, 500K)", placeholder="Unlimited")

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

def fetch_media_info_with_failover(url: str, proxy_list: list) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch video metadata with automatic failover across proxy pool and generic fallback."""
    url_candidates = get_url_candidates(url)
    attempts = proxy_list if proxy_list else [None]
    last_error = None

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

st.markdown('<div class="main-header">🎬 Universal Video Downloader</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Download videos from YouTube, social media, adult platforms, and 1000+ sites with resolution control and anti-blocking bypass.</div>', unsafe_allow_html=True)

tab_single, tab_batch, tab_guide = st.tabs(["🚀 Single URL Downloader", "📑 Batch Downloader", "📖 Bypass & Security Guide"])

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
                if view_count:
                    st.write(f"**Views:** 👁️ {view_count:,}")

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
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            cached_info = st.session_state.get("current_info")
                            if cached_info and cached_info.get("extractor") == "Universal Embedded Scraper":
                                dl_info = ydl.process_ie_result(cached_info, download=True)
                            elif cached_info and cached_info.get("webpage_url") and cached_info.get("webpage_url") != video_url:
                                dl_info = ydl.extract_info(cached_info.get("webpage_url"), download=True)
                            else:
                                dl_info = ydl.extract_info(video_url, download=True)

                            file_path = ydl.prepare_filename(dl_info)
                            
                            # If audio postprocessing happened, ext might be mp3
                            if quality_choice == "Audio Only (MP3/M4A)":
                                base, _ = os.path.splitext(file_path)
                                if os.path.exists(base + ".mp3"):
                                    file_path = base + ".mp3"

                            # If format merged to mp4
                            if not os.path.exists(file_path):
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
                            st.info("💡 Tip: Try adjusting the bypass settings in the sidebar (custom User-Agent, cookies, or proxy).")

                if download_success and file_path and os.path.exists(file_path):
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

# ----------------- TAB 3: BYPASS GUIDE -----------------
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

    #### 3. Geo-Restrictions & IP Bans
    - **Problem**: Certain videos are restricted to specific countries or your IP might be temporarily rate-limited.
    - **Solution**: Enable **Proxy** in the sidebar and enter an HTTP/HTTPS or SOCKS5 proxy URL.

    #### 4. High-Quality Video + Audio Merging (1080p+)
    - Platforms like YouTube deliver video and audio in separate streams for 1080p, 2K, and 4K resolutions.
    - `yt-dlp` automatically downloads both streams and merges them using `ffmpeg` into a single `.mp4` file.
    """)
