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
      // Build headers with optional dev-user injection for local testing
      const token = localStorage.getItem('id_token') || ''
      const devUser = process.env.NEXT_PUBLIC_DEV_USER || ''
      const headers: Record<string,string> = {'Content-Type':'application/json'}
      if(token){
        headers['Authorization'] = 'Bearer ' + token
      } else if(devUser){
        // When running in dev and backend has DEV_AUTH_BYPASS=true, inject a dev user
        headers['Authorization'] = 'Bearer dev'
        headers['X-Dev-User'] = devUser
      }

      const resp = await fetch(url, {
        method: 'POST',
        headers,
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
