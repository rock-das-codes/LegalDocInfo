import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import ChatBot from './components/interfaces/ChatUi'
import { FileUpload } from './components/interfaces/FileUpload'

function App() {
  const [documentId, setDocumentId] = useState("")

  return (
    <>
    {!documentId?(<FileUpload documentId={documentId} setDocumentId={setDocumentId}/>):null}
    {documentId&&<ChatBot documentId={documentId} />}
    </>
  )
}

export default App
