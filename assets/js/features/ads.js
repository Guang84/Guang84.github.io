const CLIENT='ca-pub-6371342728710125';
function loadAccountScript(){if(document.querySelector(`script[src*="adsbygoogle.js?client=${CLIENT}"]`))return;const s=document.createElement('script');s.async=true;s.crossOrigin='anonymous';s.src=`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${CLIENT}`;document.head.append(s)}
export function initAds(){loadAccountScript()}
