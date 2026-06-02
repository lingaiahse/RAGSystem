import {useState, useRef, useCallback} from 'react'

type Message = {text: string}

export default function useRagStream(){
  const [messages, setMessages] = useState<Message[]>([])
  const [status, setStatus] = useState<'idle'|'loading'|'error'|'done'>('idle')
  const [citations, setCitations] = useState<any[]>([])
  const controllerRef = useRef<AbortController | null>(null)

  const send = useCallback(async (query: string) =>{
    setStatus('loading')
    setMessages([])
    setCitations([])
    const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/rag/stream'
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller

    try{
      const resp = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type':'application/json', 'Authorization': 'Bearer ' + (localStorage.getItem('id_token')||'')},
        body: JSON.stringify({query, top_k:5}),
        signal: controller.signal,
      })
      if(!resp.ok) throw new Error('Network error')
      const reader = resp.body?.getReader()
      if(!reader) throw new Error('No reader')
      const decoder = new TextDecoder()
      let buf = ''
      while(true){
        const {done, value} = await reader.read()
        if(done) break
        buf += decoder.decode(value, {stream:true})
        let parts = buf.split('\n\n')
        buf = parts.pop() || ''
        for(const part of parts){
          if(!part.trim()) continue
          // SSE parsing
          const lines = part.split('\n')
          let event = 'message'
          let data = ''
          for(const line of lines){
            if(line.startsWith('event:')) event = line.replace('event:','').trim()
            if(line.startsWith('data:')) data += line.replace('data:','').trim()
          }
          if(event === 'citation'){
            try{ setCitations(JSON.parse(data)) }catch(e){console.error(e)}
          }else if(event === 'message'){
            try{ const payload = JSON.parse(data); setMessages(prev=>[...prev, {text: payload.text}]) }catch(e){console.error(e)}
          }else if(event === 'done'){
            setStatus('done')
          }
        }
      }
      setStatus('done')
    }catch(err){
      console.error(err)
      setStatus('error')
    }
  },[])

  return {messages, send, status, citations}
}
