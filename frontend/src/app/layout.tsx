import type { Metadata } from "next";
import localFont from "next/font/local";
import { Providers } from "@/lib/providers";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";
import "../styles/product-recipes.css";

const inter = localFont({
  src: "../fonts/inter-latin.woff2",
  variable: "--font-geist-sans",
  display: "swap",
});

const caveat = localFont({
  src: "../fonts/caveat-latin.woff2",
  variable: "--font-caveat",
  display: "swap",
});

export const metadata: Metadata = {
  title: "FitManager Studio+",
  description: "CRM gestionale per personal trainer - privacy first, zero cloud.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="it" suppressHydrationWarning>
      <head>
        {process.env.NODE_ENV === "development" && (
          <script
            dangerouslySetInnerHTML={{
              __html: `(function(){
  var O=window.WebSocket;
  window.WebSocket=function(u,p){
    if(typeof u==='string'&&u.includes('/_next/webpack-hmr')){
      try{var o=new URL(u);
        if(o.hostname!=='localhost'&&o.hostname!=='127.0.0.1'){
          var mock={
            readyState:1,protocol:'',extensions:'',bufferedAmount:0,binaryType:'blob',
            url:u,onopen:null,onclose:null,onerror:null,onmessage:null,
            send:function(){},close:function(){this.readyState=3;},
            addEventListener:function(){},removeEventListener:function(){},
            dispatchEvent:function(){return true}
          };
          setTimeout(function(){if(mock.onopen)mock.onopen({type:'open'});},0);
          return mock;
        }
      }catch(e){}
    }
    return p!==undefined?new O(u,p):new O(u);
  };
  window.WebSocket.prototype=O.prototype;
  window.WebSocket.CONNECTING=O.CONNECTING;
  window.WebSocket.OPEN=O.OPEN;
  window.WebSocket.CLOSING=O.CLOSING;
  window.WebSocket.CLOSED=O.CLOSED;
})();`,
            }}
          />
        )}
      </head>
      <body className={`antialiased ${inter.variable} ${caveat.variable}`}>
        <Providers>
          <TooltipProvider>{children}</TooltipProvider>
        </Providers>
      </body>
    </html>
  );
}
