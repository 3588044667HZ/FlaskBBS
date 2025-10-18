// document.querySelector("#btn").onclick = function () {
//     document.querySelector("#PhotoUploadForm").click();
// }
// let dropBox = document.getElementById('drop');
// dropBox.addEventListener('dragover', function (e) {
//     console.log('drag');
//     // 阻止事件冒泡
//     e.stopPropagation();
//     // 阻止默认事件（与drop事件结合，阻止拖拽文件在浏览器打开的默认行为）
//     e.preventDefault();
// });


onUpload = function (e) {

    console.log(e.dataTransfer);
    let postForm = document.getElementById("postForm");
    let tempDiv = document.createElement('div');
    tempDiv.innerText = `pic ${e.dataTransfer.files[0].name} uploading... 0%`;
    postForm.appendChild(tempDiv);
    upload(e.dataTransfer.files[0], (result) => {
        console.log(result);
        // 显示缩略图
        tempDiv.innerText = '';
        let pic = document.createElement('img');
        document.getElementById("markdownEditor").innerText = document.getElementById("markdownEditor").innerText + `[!pic src=/static/pics${result['path']}.png]`
        reader = new FileReader();
        reader.readAsDataURL(e.dataTransfer.files[0]);
        reader.onload = e => {
            pic.src = e.target.result;
        }
        // pic.src = e.dataTransfer.files[0];
        document.getElementById("postForm").appendChild(pic)
    }, (progress) => {
        tempDiv.innerText = `pic ${e.dataTransfer.files[0].name} uploading... ${progress}%`;


    })


}

function upload(file, onFinished, onError) {
    let uploader = new XMLHttpRequest();
    uploader.upload.onprogress = e => {
        console.log(e);
        // onProgress(e);

    }
    let fileData = new FormData();
    uploader.onload = () => {
        const resp = JSON.parse(uploader.responseText);
        onFinished(resp["path"]);

    }
    uploader.onerror = (ev) => {
        onError(ev);
    }
    uploader.open("POST", "/upload/pic");

    // const
    fileData.append("pic", file);
    fileData.append('enctype', "multipart/form-data");
    // fileData.append('content-type', "image/jpeg");
    uploader.send(fileData);
}

// dropBox.addEventListener('dragover', function (e) {
//     // 阻止事件冒泡
//     e.stopPropagation();
//     // 阻止默认事件（与drop事件结合，阻止拖拽文件在浏览器打开的默认行为）
//     e.preventDefault();
//     onUpload(e);
// });