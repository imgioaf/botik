import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'Ksey Bank - Telegram Wallet',
  description: 'Secure crypto wallet and banking for Telegram',
  viewport: 'width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no',
  themeColor: '#0f1419',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style jsx global>{`
          :root {
            color-scheme: dark;
          }
        `}</style>
      </head>
      <body 
        className={`${inter.className} ${mono.variable} bg-liquid-dark text-white overflow-x-hidden antialiased`}
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  )
}
