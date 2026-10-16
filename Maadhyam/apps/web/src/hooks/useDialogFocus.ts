import { useEffect, useRef } from 'react';

/** Keep keyboard focus inside a displayed modal and return it to the opener. */
export function useDialogFocus(active:boolean, selector:string, close:()=>void) {
  const closeRef=useRef(close);
  useEffect(()=>{closeRef.current=close;},[close]);
  useEffect(()=>{
    if(!active)return;
    const previous=document.activeElement instanceof HTMLElement?document.activeElement:null;
    const dialog=document.querySelector<HTMLElement>(selector);
    if(!dialog)return;
    const focusable=()=>Array.from(dialog.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]')).filter(e=>e.getClientRects().length>0);
    focusable()[0]?.focus();
    const keydown=(event:KeyboardEvent)=>{
      if(event.key==='Escape'){event.preventDefault();closeRef.current();return;}
      if(event.key!=='Tab')return;
      const items=focusable();
      const first=items[0],last=items.at(-1);
      if(!first)return;
      if(event.shiftKey&&(document.activeElement===first||!dialog.contains(document.activeElement))){event.preventDefault();last?.focus();}
      else if(!event.shiftKey&&(document.activeElement===last||!dialog.contains(document.activeElement))){event.preventDefault();first.focus();}
    };
    document.addEventListener('keydown',keydown);
    return()=>{document.removeEventListener('keydown',keydown);if(previous?.isConnected)previous.focus();};
  },[active,selector]);
}
