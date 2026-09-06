const $=id=>document.getElementById(id);
let ctx, sources=[], muted=false, lastUrl;
$('stop').onclick=()=>{muted=true;sources.forEach(s=>{try{s.stop()}catch{}});$('stop').disabled=true;};
$('run').onclick=async()=>{
  const text=$('text').value.trim(); if(!text)return;
  $('run').disabled=true;$('stop').disabled=false;$('download').hidden=true;muted=false;sources=[];
  if(ctx)await ctx.close();ctx=new AudioContext({sampleRate:24000});await ctx.resume();
  const start=performance.now();let first=null,total=0,count=0,next=ctx.currentTime,gaps=0,pcm=[];
  const update=()=>{$('status').textContent=`${first===null?'等待首段音频…':`首段到达：${first.toFixed(2)} 秒`}\n已收到 ${count} 段 · 音频 ${total.toFixed(2)} 秒 · 耗时 ${((performance.now()-start)/1000).toFixed(2)} 秒${gaps?` · 播放断流 ${gaps} 次`:''}`;};
  update();
  try{
    const response=await fetch('/speech',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:'breeze-tts-2',input:text,response_format:'pcm',stream_format:'sse',options:{instruction:$('instruction').value,text_chunk_size:Number($('chunk').value),guidance_scale:Number($('cfg').value),seed:42}})});
    if(!response.ok)throw Error(await response.text());
    const reader=response.body.getReader(),decoder=new TextDecoder();let pending='';
    while(true){const {value,done}=await reader.read();if(done)break;pending+=decoder.decode(value,{stream:true});let pos;
      while((pos=pending.indexOf('\n'))>=0){const line=pending.slice(0,pos).trim();pending=pending.slice(pos+1);if(!line.startsWith('data: '))continue;const raw=line.slice(6);if(raw==='[DONE]')continue;
        const e=JSON.parse(raw);if(e.type==='error'||e.error)throw Error(JSON.stringify(e));if(e.type!=='speech.audio.delta')continue;
        const bytes=Uint8Array.from(atob(e.audio),c=>c.charCodeAt(0));pcm.push(bytes);const view=new DataView(bytes.buffer),n=bytes.length/2;
        const buffer=ctx.createBuffer(1,n,24000),data=buffer.getChannelData(0);for(let i=0;i<n;i++)data[i]=view.getInt16(i*2,true)/32768;
        if(first===null)first=(performance.now()-start)/1000;
        if(count&&ctx.currentTime>next+.05)gaps++;
        if(!muted){const source=ctx.createBufferSource();source.buffer=buffer;source.connect(ctx.destination);next=Math.max(next,ctx.currentTime+.03);source.start(next);next+=buffer.duration;sources.push(source);}
        total+=n/24000;count++;update();
      }
    }
    if(!count)throw Error('未收到音频');
    const wall=(performance.now()-start)/1000;update();$('status').textContent+=`\n生成完成 · RTF ${(wall/total).toFixed(3)} · ${(total/wall).toFixed(2)} 倍实时速度`;
    const size=pcm.reduce((s,a)=>s+a.length,0),header=new ArrayBuffer(44),v=new DataView(header);const str=(o,s)=>[...s].forEach((c,i)=>v.setUint8(o+i,c.charCodeAt(0)));
    str(0,'RIFF');v.setUint32(4,36+size,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,24000,true);v.setUint32(28,48000,true);v.setUint16(32,2,true);v.setUint16(34,16,true);str(36,'data');v.setUint32(40,size,true);
    if(lastUrl)URL.revokeObjectURL(lastUrl);lastUrl=URL.createObjectURL(new Blob([header,...pcm],{type:'audio/wav'}));$('download').href=lastUrl;$('download').download='breeze-tts-2.wav';$('download').hidden=false;
  }catch(e){$('status').textContent+='\n生成失败：'+e.message;}finally{$('run').disabled=false;}
};
