'use client'

import { useEffect, useState } from 'react'
import { Wallet, Send, ArrowUp, History, Lock, Smartphone, LogOut } from 'lucide-react'

interface TelegramWebApp {
  ready: () => void
  expand: () => void
  sendData: (data: string) => void
  close: () => void
  MainButton: any
  HapticFeedback: any
  initDataUnsafe: any
  user: any
}

export default function App() {
  const [balance, setBalance] = useState('0.00')
  const [screen, setScreen] = useState<'home' | 'deposit' | 'withdraw' | 'transfer' | 'history' | '2fa' | 'devices'>('home')
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Initialize Telegram Web App
    const tg = (window as any).Telegram?.WebApp
    if (tg) {
      tg.ready()
      tg.expand()
      tg.setHeaderColor('#0f1419')
      tg.setBackgroundColor('#0f1419')
      
      if (tg.initDataUnsafe?.user) {
        setUser(tg.initDataUnsafe.user)
      }

      // Haptic feedback on mount
      tg.HapticFeedback?.impactOccurred?.('light')
    }

    // Fetch user balance
    fetchBalance()
  }, [])

  const fetchBalance = async () => {
    try {
      const response = await fetch('/api/wallet/balance')
      const data = await response.json()
      setBalance(data.balance || '0.00')
    } catch (error) {
      console.error('Error fetching balance:', error)
    }
  }

  const handleAction = (action: string) => {
    const tg = (window as any).Telegram?.WebApp
    tg?.HapticFeedback?.impactOccurred?.('medium')
    
    setLoading(true)
    // Simulate API call
    setTimeout(() => {
      setLoading(false)
      setScreen(action as any)
    }, 200)
  }

  const handleBackToHome = () => {
    setScreen('home')
  }

  // Home Screen
  if (screen === 'home') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-liquid-dark to-liquid-base pb-32">
        {/* Header */}
        <div className="glass-card m-4 p-6 text-center">
          <div className="text-sm text-gray-400 mb-2">Total Balance</div>
          <div className="text-4xl font-bold gradient-text">${balance}</div>
          <div className="text-xs text-gray-500 mt-2">USDT</div>
        </div>

        {/* User Info */}
        {user && (
          <div className="mx-4 mt-4 glass-card p-4 flex items-center gap-3">
            {user.photo_url && (
              <img src={user.photo_url} alt={user.first_name} className="w-10 h-10 rounded-full" />
            )}
            <div>
              <div className="font-semibold">{user.first_name} {user.last_name || ''}</div>
              <div className="text-xs text-gray-400">@{user.username}</div>
            </div>
          </div>
        )}

        {/* Action Grid */}
        <div className="grid grid-cols-2 gap-3 p-4">
          <button
            onClick={() => handleAction('deposit')}
            className="glass-card-hover p-4 text-center space-y-2 group"
          >
            <div className="mx-auto w-12 h-12 bg-gradient-to-br from-liquid-accent/20 to-transparent rounded-xl flex items-center justify-center group-hover:from-liquid-accent/40 transition">
              <ArrowUp className="w-6 h-6 text-liquid-accent" />
            </div>
            <div className="font-semibold text-sm">Deposit</div>
          </button>

          <button
            onClick={() => handleAction('withdraw')}
            className="glass-card-hover p-4 text-center space-y-2 group"
          >
            <div className="mx-auto w-12 h-12 bg-gradient-to-br from-liquid-accent/20 to-transparent rounded-xl flex items-center justify-center group-hover:from-liquid-accent/40 transition">
              <ArrowUp className="w-6 h-6 text-liquid-accent rotate-180" />
            </div>
            <div className="font-semibold text-sm">Withdraw</div>
          </button>

          <button
            onClick={() => handleAction('transfer')}
            className="glass-card-hover p-4 text-center space-y-2 group"
          >
            <div className="mx-auto w-12 h-12 bg-gradient-to-br from-liquid-accent/20 to-transparent rounded-xl flex items-center justify-center group-hover:from-liquid-accent/40 transition">
              <Send className="w-6 h-6 text-liquid-accent" />
            </div>
            <div className="font-semibold text-sm">Transfer</div>
          </button>

          <button
            onClick={() => handleAction('history')}
            className="glass-card-hover p-4 text-center space-y-2 group"
          >
            <div className="mx-auto w-12 h-12 bg-gradient-to-br from-liquid-accent/20 to-transparent rounded-xl flex items-center justify-center group-hover:from-liquid-accent/40 transition">
              <History className="w-6 h-6 text-liquid-accent" />
            </div>
            <div className="font-semibold text-sm">History</div>
          </button>

          <button
            onClick={() => handleAction('2fa')}
            className="glass-card-hover p-4 text-center space-y-2 group"
          >
            <div className="mx-auto w-12 h-12 bg-gradient-to-br from-liquid-accent/20 to-transparent rounded-xl flex items-center justify-center group-hover:from-liquid-accent/40 transition">
              <Lock className="w-6 h-6 text-liquid-accent" />
            </div>
            <div className="font-semibold text-sm">2FA</div>
          </button>

          <button
            onClick={() => handleAction('devices')}
            className="glass-card-hover p-4 text-center space-y-2 group"
          >
            <div className="mx-auto w-12 h-12 bg-gradient-to-br from-liquid-accent/20 to-transparent rounded-xl flex items-center justify-center group-hover:from-liquid-accent/40 transition">
              <Smartphone className="w-6 h-6 text-liquid-accent" />
            </div>
            <div className="font-semibold text-sm">Devices</div>
          </button>
        </div>

        {/* Recent Transactions */}
        <div className="mx-4 mt-6 glass-card p-4">
          <h3 className="font-semibold mb-4">Recent Activity</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center py-2 border-b border-glass-200">
              <div>
                <div className="font-semibold">Received USDT</div>
                <div className="text-xs text-gray-500">2 hours ago</div>
              </div>
              <div className="text-green-400">+100.00</div>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-glass-200">
              <div>
                <div className="font-semibold">Sent USDT</div>
                <div className="text-xs text-gray-500">5 hours ago</div>
              </div>
              <div className="text-red-400">-50.00</div>
            </div>
            <div className="flex justify-between items-center py-2">
              <div>
                <div className="font-semibold">Deposit ETH</div>
                <div className="text-xs text-gray-500">1 day ago</div>
              </div>
              <div className="text-green-400">+1.50</div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Deposit Screen
  if (screen === 'deposit') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-liquid-dark to-liquid-base pb-32">
        <div className="p-4 space-y-4">
          <button onClick={handleBackToHome} className="text-liquid-accent mb-4">← Back</button>
          <h1 className="text-2xl font-bold">Deposit</h1>
          <div className="glass-card p-6 space-y-4">
            <div>
              <label className="text-sm text-gray-400">Select Currency</label>
              <select className="w-full mt-2 bg-glass-100 border border-glass-200 rounded-lg p-3 text-white">
                <option>USDT</option>
                <option>ETH</option>
                <option>BTC</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-400">Deposit Address</label>
              <div className="mt-2 bg-glass-100 border border-glass-200 rounded-lg p-3 font-mono text-xs break-all">
                TQGdfAKdmZXiJ3j3Ks4K9Q9pRo8X7Q3J4M
              </div>
              <button className="w-full mt-2 text-liquid-accent text-sm hover:text-liquid-light transition">
                Copy Address
              </button>
            </div>
            <button className="liquid-btn w-full mt-4">Show QR Code</button>
          </div>
        </div>
      </div>
    )
  }

  // Withdraw Screen
  if (screen === 'withdraw') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-liquid-dark to-liquid-base pb-32">
        <div className="p-4 space-y-4">
          <button onClick={handleBackToHome} className="text-liquid-accent mb-4">← Back</button>
          <h1 className="text-2xl font-bold">Withdraw</h1>
          <div className="glass-card p-6 space-y-4">
            <div>
              <label className="text-sm text-gray-400">Amount</label>
              <input type="number" placeholder="100.00" className="w-full mt-2 bg-glass-100 border border-glass-200 rounded-lg p-3" />
            </div>
            <div>
              <label className="text-sm text-gray-400">Destination Address</label>
              <input type="text" placeholder="Enter address..." className="w-full mt-2 bg-glass-100 border border-glass-200 rounded-lg p-3" />
            </div>
            <button className="liquid-btn w-full mt-4">Withdraw</button>
          </div>
        </div>
      </div>
    )
  }

  // Transfer Screen
  if (screen === 'transfer') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-liquid-dark to-liquid-base pb-32">
        <div className="p-4 space-y-4">
          <button onClick={handleBackToHome} className="text-liquid-accent mb-4">← Back</button>
          <h1 className="text-2xl font-bold">Transfer</h1>
          <div className="glass-card p-6 space-y-4">
            <div>
              <label className="text-sm text-gray-400">Send To (Username)</label>
              <input type="text" placeholder="@username" className="w-full mt-2 bg-glass-100 border border-glass-200 rounded-lg p-3" />
            </div>
            <div>
              <label className="text-sm text-gray-400">Amount</label>
              <input type="number" placeholder="0.00" className="w-full mt-2 bg-glass-100 border border-glass-200 rounded-lg p-3" />
            </div>
            <button className="liquid-btn w-full mt-4">Send</button>
          </div>
        </div>
      </div>
    )
  }

  // History Screen
  if (screen === 'history') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-liquid-dark to-liquid-base pb-32">
        <div className="p-4 space-y-4">
          <button onClick={handleBackToHome} className="text-liquid-accent mb-4">← Back</button>
          <h1 className="text-2xl font-bold">Transaction History</h1>
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="glass-card p-4 flex justify-between items-center">
                <div>
                  <div className="font-semibold text-sm">Transaction #{i + 1}</div>
                  <div className="text-xs text-gray-500">2 days ago</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold">+100 USDT</div>
                  <div className="text-xs text-green-400">Completed</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // 2FA Screen
  if (screen === '2fa') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-liquid-dark to-liquid-base pb-32">
        <div className="p-4 space-y-4">
          <button onClick={handleBackToHome} className="text-liquid-accent mb-4">← Back</button>
          <h1 className="text-2xl font-bold">Two-Factor Authentication</h1>
          <div className="glass-card p-6 space-y-4">
            <div className="flex items-center justify-between p-4 bg-glass-100 rounded-lg">
              <div>
                <div className="font-semibold">2FA Status</div>
                <div className="text-sm text-gray-400">TOTP Enabled</div>
              </div>
              <div className="w-3 h-3 bg-green-400 rounded-full"></div>
            </div>
            <div className="text-sm text-gray-400 space-y-2">
              <p>✓ Authenticator app enabled</p>
              <p>✓ Backup codes saved</p>
              <p>✓ Device whitelist active</p>
            </div>
            <button className="liquid-btn w-full mt-4">Manage Settings</button>
          </div>
        </div>
      </div>
    )
  }

  // Devices Screen
  if (screen === 'devices') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-liquid-dark to-liquid-base pb-32">
        <div className="p-4 space-y-4">
          <button onClick={handleBackToHome} className="text-liquid-accent mb-4">← Back</button>
          <h1 className="text-2xl font-bold">Approved Devices</h1>
          <div className="space-y-2">
            {[
              { name: 'iPhone 15 Pro', os: 'iOS 17', last: 'Now' },
              { name: 'MacBook Pro', os: 'macOS Sonoma', last: '2 hours ago' },
              { name: 'Android Phone', os: 'Android 14', last: '1 day ago' },
            ].map((device, i) => (
              <div key={i} className="glass-card p-4 flex justify-between items-center">
                <div>
                  <div className="font-semibold text-sm">{device.name}</div>
                  <div className="text-xs text-gray-500">{device.os} • {device.last}</div>
                </div>
                <button className="text-red-400 text-sm hover:text-red-300">Remove</button>
              </div>
            ))}
          </div>
          <button className="border border-glass-200 w-full p-3 rounded-lg text-sm mt-4 hover:bg-glass-100 transition">
            + Add New Device
          </button>
        </div>
      </div>
    )
  }

  return null
}
