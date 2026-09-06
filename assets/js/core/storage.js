export function getPref(key,fallback){try{return localStorage.getItem(key)??fallback}catch{return fallback}}export function setPref(key,value){try{localStorage.setItem(key,value)}catch{}}
