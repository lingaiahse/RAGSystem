import React from 'react'

export default function ChatMessage({message, citations}:{message:{text:string}, citations:any[]}){
  return (
    <div className="p-3 border rounded">
      <div className="prose">
        {message.text}
      </div>
      {citations && citations.length>0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {citations.map((c:any, i:number)=>(
            <button key={i} onClick={()=>alert(JSON.stringify(c, null, 2))} className="px-2 py-1 bg-gray-100 border rounded text-sm">{c.source}{c.page?`:${c.page}`:''}</button>
          ))}
        </div>
      )}
    </div>
  )
}
