import { useState } from 'react';

export default function FilePicker({ onFileSelect }) {
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
    onFileSelect(file);
  };

  return (
    <div className="file-picker flex items-center">
      <input
        type="file"
        onChange={handleFileChange}
        className="p-2 border border-gray-300 rounded"
      />
      {selectedFile && <span className="ml-2">{selectedFile.name}</span>}
    </div>
  );
}
