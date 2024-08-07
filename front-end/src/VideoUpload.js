import React, { useState } from 'react';
import './App.css';

function VideoUpload() {
  const [caption, setCaption] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  function handleUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const chunkSize = 2 * 1024 * 1024;  // 2MB
    const totalChunks = Math.ceil(file.size / chunkSize);
    let chunkIndex = 0;

    const uploadChunk = (chunk) => {
      const formData = new FormData();
      formData.append('file', chunk);
      formData.append('index', chunkIndex);
      formData.append('filename', file.name);

      console.log(`Uploading chunk ${chunkIndex + 1}/${totalChunks}`);

      fetch('http://localhost:5000/upload-chunk', {
        method: 'POST',
        body: formData,
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json().catch(err => {
          throw new Error('Invalid JSON: ' + err.message);
        });
      })
      .then(data => {
        console.log('Chunk upload successful', data);
        chunkIndex++;
        setProgress((chunkIndex / totalChunks) * 100);
        if (chunkIndex < totalChunks) {
          const start = chunkIndex * chunkSize;
          const end = Math.min(file.size, start + chunkSize);
          const nextChunk = file.slice(start, end);
          uploadChunk(nextChunk);
        } else {
          setCaption('All chunks uploaded successfully.');
          setUploading(false);
          // Notify the server to reassemble the chunks
          fetch('http://localhost:5000/reassemble-video', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename: file.name }),
          })
          .then(response => {
            if (!response.ok) {
              throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json().catch(err => {
              throw new Error('Invalid JSON: ' + err.message);
            });
          })
          .then(data => {
            console.log('Reassembly successful', data);
            setCaption('Video reassembled successfully.');
          })
          .catch(error => {
            console.error('Error reassembling video:', error);
            setCaption('Failed to reassemble video.');
          });
        }
      })
      .catch(error => {
        console.error('Error uploading chunk:', error);
        setCaption('Failed to upload chunks.');
        setUploading(false);
      });
    };
    console.log("Called");
    // Start uploading the first chunk
    setUploading(true);
    const start = chunkIndex * chunkSize;
    const end = Math.min(file.size, start + chunkSize);
    const firstChunk = file.slice(start, end);
    uploadChunk(firstChunk);
  }

  return (
    <div>
      <h1>Upload Video</h1>
      <input type="file" accept="video/*" onChange={handleUpload} disabled={uploading} />
      {uploading && <div className="progress" style={{ '--progress': `${progress}%` }}></div>}
      {caption && <div className="caption">{caption}</div>}
    </div>
  );
}

export default VideoUpload;
