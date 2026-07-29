import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'

// Verify Telegram WebApp data
export async function POST(request: NextRequest) {
  try {
    const { initData } = await request.json()

    // Parse the init data from Telegram
    const params = new URLSearchParams(initData)
    const hash = params.get('hash')
    
    // Remove hash from params for verification
    params.delete('hash')

    // Sort parameters alphabetically
    const dataCheckString = Array.from(params.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => `${key}=${value}`)
      .join('\n')

    // Verify hash (using your BOT_TOKEN)
    const botToken = process.env.TELEGRAM_BOT_TOKEN || ''
    const secretKey = crypto
      .createHmac('sha256', 'WebAppData')
      .update(botToken)
      .digest()

    const calculatedHash = crypto
      .createHmac('sha256', secretKey)
      .update(dataCheckString)
      .digest('hex')

    if (hash !== calculatedHash) {
      return NextResponse.json(
        { error: 'Invalid data' },
        { status: 403 }
      )
    }

    // Extract user data
    const userJson = params.get('user')
    const user = userJson ? JSON.parse(userJson) : null

    return NextResponse.json({
      valid: true,
      user: user,
      timestamp: Date.now(),
    })
  } catch (error) {
    console.error('Telegram verification error:', error)
    return NextResponse.json(
      { error: 'Verification failed' },
      { status: 400 }
    )
  }
}
