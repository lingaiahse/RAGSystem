"use client"
import React, {useState} from 'react'
import useRagStream from '../hooks/useRagStream'
import ChatMessage from '../components/ChatMessage'

export default function Page(){
  const [query, setQuery] = useState('')
  const {messages, send, status, citations} = useRagStream()

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">Enterprise HR Policy Assistant</h1>
      <div className="space-y-4">
        {messages.map((m, i) => <ChatMessage key={i} message={m} citations={citations} />)}
      </div>
      <form onSubmit={e=>{e.preventDefault(); send(query); setQuery('')}} className="mt-4 flex gap-2">
        <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ask a policy question..." className="flex-1 p-2 border rounded" />
        <button className="px-4 py-2 bg-sky-600 text-white rounded">Ask</button>
      </form>
      <div className="text-sm text-muted mt-2">Status: {status}</div>
    </div>
  )
}
