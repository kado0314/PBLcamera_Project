document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('imageInput');
    const imagePreview = document.getElementById('imagePreview');
    const openCameraBtn = document.getElementById('openCameraBtn');
    const cameraArea = document.getElementById('cameraArea');
    const cameraVideo = document.getElementById('cameraVideo');
    const takePhotoBtn = document.getElementById('takePhotoBtn');
    let stream = null;

    // ファイル選択時のプレビュー
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
            }
            reader.readAsDataURL(file);
        }
    });

    // カメラ起動
    openCameraBtn.addEventListener('click', async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: "environment" } 
            });
            cameraVideo.srcObject = stream;
            cameraArea.style.display = 'block';
            openCameraBtn.style.display = 'none';
        } catch (err) {
            console.error("Camera Error:", err);
            alert("カメラを起動できませんでした。");
        }
    });

    // 撮影
    takePhotoBtn.addEventListener('click', () => {
        const canvas = document.createElement('canvas');
        canvas.width = cameraVideo.videoWidth;
        canvas.height = cameraVideo.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(cameraVideo, 0, 0);
        
        canvas.toBlob((blob) => {
            const file = new File([blob], "camera_photo.jpg", { type: "image/jpeg" });
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            imageInput.files = dataTransfer.files;

            // プレビュー更新
            imagePreview.src = canvas.toDataURL('image/jpeg');
            imagePreview.style.display = 'block';

            // カメラ停止
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            cameraArea.style.display = 'none';
            openCameraBtn.style.display = 'inline-block';
        }, 'image/jpeg');
    });
});
