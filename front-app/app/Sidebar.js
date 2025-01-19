export default function Sidebar({ assistants, setShowModal, removeAssistant }) {
  return (
    <div className="sidebar w-1/4 bg-gray-800 text-white p-5">
      <h2 className="text-2xl font-bold mb-5">Sidebar</h2>
      <ul>
        {assistants.map((assistant) => (
          <li key={assistant.id} className="mb-3 flex justify-between items-center">
            <a
              href="#"
              className="hover:underline max-w-xs overflow-hidden block whitespace-nowrap text-ellipsis"
              style={{ maxWidth: '320px' }}
            >
              {assistant.name}
            </a>
            <button onClick={() => removeAssistant(assistant.id)} className="ml-2 text-red-500 hover:text-red-700">
              &#x2716; {/* Unicode for a cross mark */}
            </button>
          </li>
        ))}
      </ul>
      <button
        onClick={() => setShowModal(true)}
        className="mt-5 p-2 bg-blue-500 text-white rounded hover:bg-blue-700"
      >
        Add Assistant
      </button>
    </div>
  );
}
