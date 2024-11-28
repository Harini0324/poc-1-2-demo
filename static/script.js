const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const output = document.getElementById('output');
const captureButton = document.getElementById('capture');

let stream;

navigator.mediaDevices.getUserMedia({ video: true })
    .then(function (mediaStream) {
        stream = mediaStream;
        video.srcObject = stream;
        video.play();
    })
    .catch(function (err) {
        console.log("Error accessing camera:", err);
    });

captureButton.addEventListener('click', function () {
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    const imageData = canvas.toDataURL('image/jpeg', 1.0);

    fetch('/process_image', {
        method: 'POST',
        body: JSON.stringify({ imageData: imageData }),
        headers: { 'Content-Type': 'application/json' }
    })
        .then(response => response.json())
        .then(data => {
            output.textContent = data.message;
        })
        .catch(error => {
            console.error("Error sending image to backend:", error);
            output.textContent = "An error occurred. Please try again.";
        });
});

window.onbeforeunload = function (e) {
    stream.getTracks().forEach(track => {
        track.stop();
    });
};
