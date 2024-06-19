// Function to get current time of the video
function getCurrentTime() {
  let video = document.querySelector('video');
  if (video) {
    let currentTime = video.currentTime;
    let videoDetails = getVideoDetails();
    sendTimeToServer(currentTime, videoDetails);
  }
}

// Function to get video details such as title, ID and subtitles
function getVideoDetails() {
  let videoDetails = {};
  
  // Get video title
  // let titleElement = document.querySelector('yt-formatted-string');
  // videoDetails.title = titleElement ? titleElement.innerText : 'Unknown Title';

  // Get video ID from URL
  let urlParams = new URLSearchParams(window.location.search);
  videoDetails.videoId = urlParams.get('v') ? urlParams.get('v') : 'Unknown ID';

  // Get subtitles (if available)
  // let captionsTracks = Array.from(document.querySelectorAll('ytd-transcript-body-renderer yt-transcript-segment-list-renderer')).map(track => track.innerText);
  // videoDetails.subtitles = captionsTracks;

  return videoDetails;
}

// Function to send time and video details to the server
function sendTimeToServer(time, details) {
  fetch('http://localhost:5000/video_content', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ 'time': time, 'details': details })
  });
}

// Run getCurrentTime every second
setInterval(getCurrentTime, 1000);
