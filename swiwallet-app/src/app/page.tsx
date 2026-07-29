'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Lock, Zap, Users, ShieldCheck, Send, Smartphone } from 'lucide-react'

export default function Home() {
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <main className="relative min-h-screen bg-gradient-to-b from-liquid-dark via-liquid-base to-liquid-dark overflow-hidden">
      {/* Animated background gradient */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-liquid-accent/5 via-transparent to-liquid-accent/5 opacity-30"></div>
        <div className="absolute top-1/4 right-0 w-96 h-96 bg-liquid-accent/5 rounded-full blur-3xl -mr-48"></div>
        <div className="absolute bottom-1/4 left-0 w-96 h-96 bg-liquid-accent/5 rounded-full blur-3xl -ml-48"></div>
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-glass-50 border-b border-glass-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold gradient-text">Ksey Bank</div>
          <div className="hidden md:flex space-x-8">
            <Link href="#features" className="text-sm hover:text-liquid-accent transition">Features</Link>
            <Link href="#security" className="text-sm hover:text-liquid-accent transition">Security</Link>
            <Link href="#faq" className="text-sm hover:text-liquid-accent transition">FAQ</Link>
            <Link href="#contact" className="text-sm hover:text-liquid-accent transition">Contact</Link>
          </div>
          <Link href="/app">
            <button className="liquid-btn text-sm">Open App</button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 pt-32 pb-20 px-4 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            <span className="gradient-text">Secure Banking</span>
            <br />
            for Telegram
          </h1>
          <p className="text-lg md:text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            Manage your crypto assets with enterprise-grade security. Fast transfers, multi-currency support, and 2FA authentication.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link href="/app">
              <button className="liquid-btn w-full sm:w-auto flex items-center justify-center gap-2">
                Launch App <ArrowRight size={18} />
              </button>
            </Link>
            <button className="px-6 py-3 rounded-lg border border-glass-200 hover:bg-glass-100 transition">
              Learn More
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mt-12">
            <div className="glass-card p-4">
              <div className="text-2xl font-bold text-liquid-accent">50K+</div>
              <div className="text-sm text-gray-400">Active Users</div>
            </div>
            <div className="glass-card p-4">
              <div className="text-2xl font-bold text-liquid-accent">$500M+</div>
              <div className="text-sm text-gray-400">Transactions</div>
            </div>
            <div className="glass-card p-4">
              <div className="text-2xl font-bold text-liquid-accent">99.9%</div>
              <div className="text-sm text-gray-400">Uptime</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative z-10 py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-12 gradient-text">Features</h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: Send, title: 'Instant Transfers', desc: 'Send crypto instantly to any Telegram user' },
              { icon: Lock, title: 'Secure Wallet', desc: 'AES-256 encryption with 2FA authentication' },
              { icon: Zap, title: 'Fast & Cheap', desc: 'Ultra-low fees with instant settlement' },
              { icon: ShieldCheck, title: 'Device Whitelist', desc: 'Approve devices for extra security' },
              { icon: Users, title: 'Split Bills', desc: 'Easily split payments with friends' },
              { icon: Smartphone, title: 'Mobile First', desc: 'Beautiful UI optimized for mobile' },
            ].map((feature, i) => (
              <div key={i} className="glass-card-hover p-6">
                <feature.icon className="w-12 h-12 text-liquid-accent mb-4" />
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-gray-400 text-sm">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security Section */}
      <section id="security" className="relative z-10 py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-12 gradient-text">Bank-Grade Security</h2>
          
          <div className="glass-card p-8 md:p-12">
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-2xl font-bold mb-4">Encryption</h3>
                <ul className="space-y-3 text-gray-300">
                  <li>✓ AES-256-GCM encryption</li>
                  <li>✓ End-to-end encrypted communication</li>
                  <li>✓ Secure key storage</li>
                  <li>✓ Regular security audits</li>
                </ul>
              </div>
              <div>
                <h3 className="text-2xl font-bold mb-4">Authentication</h3>
                <ul className="space-y-3 text-gray-300">
                  <li>✓ 2FA TOTP (Time-based)</li>
                  <li>✓ Device whitelisting</li>
                  <li>✓ Backup codes</li>
                  <li>✓ Session management</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="relative z-10 py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-12 gradient-text">FAQ</h2>
          
          <div className="space-y-4">
            {[
              {
                q: 'How do I get started?',
                a: 'Simply open the Telegram bot and tap "Open App". Your account is created instantly.'
              },
              {
                q: 'Is my data secure?',
                a: 'Yes, we use bank-grade AES-256 encryption and TOTP 2FA authentication for all accounts.'
              },
              {
                q: 'What cryptocurrencies are supported?',
                a: 'We support TON, USDT, ETH, BTC, BNB, SOL, ADA, XRP, DOGE, and MATIC.'
              },
              {
                q: 'Are there any fees?',
                a: 'We charge minimal fees only for on-chain transactions. P2P transfers are free.'
              },
              {
                q: 'How do I withdraw?',
                a: 'Navigate to Withdraw in the app, select your crypto, and provide a destination address.'
              },
              {
                q: 'What about customer support?',
                a: 'We provide 24/7 support via Telegram. Message @kseybot for assistance.'
              },
            ].map((faq, i) => (
              <details key={i} className="glass-card p-6 cursor-pointer group">
                <summary className="font-semibold flex justify-between items-center">
                  {faq.q}
                  <span className="text-liquid-accent group-open:rotate-180 transition">▼</span>
                </summary>
                <p className="mt-4 text-gray-400 text-sm">{faq.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 py-20 px-4 text-center">
        <div className="max-w-2xl mx-auto glass-card p-12">
          <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
          <p className="text-gray-400 mb-8">Join thousands of users managing their crypto on Telegram.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="https://t.me/kseybot">
              <button className="liquid-btn flex items-center justify-center gap-2">
                Open Telegram Bot <ArrowRight size={18} />
              </button>
            </Link>
            <a href="https://t.me/kseychannel">
              <button className="px-6 py-3 rounded-lg border border-glass-200 hover:bg-glass-100 transition">
                Join Channel
              </button>
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-glass-200 py-8 px-4">
        <div className="max-w-6xl mx-auto text-center text-sm text-gray-400">
          <p>&copy; 2026 Ksey Bank. All rights reserved.</p>
          <div className="mt-4 flex justify-center gap-6">
            <a href="https://twitter.com/kseybank" className="hover:text-liquid-accent transition">Twitter</a>
            <a href="https://t.me/kseychannel" className="hover:text-liquid-accent transition">Telegram</a>
            <a href="mailto:support@kseybank.io" className="hover:text-liquid-accent transition">Support</a>
          </div>
        </div>
      </footer>
    </main>
  )
}
