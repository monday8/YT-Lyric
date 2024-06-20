########## yt-dlp ###########
import yt_dlp
import json

# YT-dlp選項
ytdlp_options = {
    'quiet': True,
    'skip_download': True,
    'writeinfojson': True
}

def lyric_lang(current_url):
    # 排除縮小導致沒有網址可以讀
    if current_url == 'Unknown ID':
        return None
    # URL
    video_url = 'https://www.youtube.com/watch?v='+current_url
    
    # 使用 yt-dlp獲取訊息
    with yt_dlp.YoutubeDL(ytdlp_options) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)

    # 提取字幕信息
    subtitles = info_dict.get('subtitles', {})
    automatic_captions = info_dict.get('automatic_captions', {})

    lyric_lang_list = {}
    for lang, subs in subtitles.items():
        # 排除自動翻譯的
        if lang != 'live_chat':
            lyric_lang_list[lang] = subs[0]['url']
    
    return lyric_lang_list if lyric_lang_list else None
def parse_srt_content(srt_content):
    
    data = json.loads(srt_content)
    events = data.get('events',[])
    return events

def getlyric(sub_url):
    with yt_dlp.YoutubeDL(ytdlp_options).urlopen(sub_url) as response:
        subtitles_content = response.read().decode('utf-8')
        lyric_contnet = parse_srt_content(subtitles_content)

    return lyric_contnet