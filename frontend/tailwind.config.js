/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
        "./public/index.html"
    ],
    theme: {
        extend: {
            fontFamily: {
                cinzel: ['Cinzel', 'serif'],
                manrope: ['Manrope', 'sans-serif'],
                playfair: ['Playfair Display', 'serif'],
            },
            colors: {
                // Royal Theme Colors
                royal: {
                    bg: '#0F0518',
                    paper: '#1A0B2E',
                    surface: '#240F3E',
                },
                gold: {
                    DEFAULT: '#FFD700',
                    start: '#FFD700',
                    mid: '#FDB931',
                    end: '#D97706',
                },
                purple: {
                    deep: '#4C1D95',
                    vivid: '#7C3AED',
                    neon: '#D946EF',
                },
                // Shadcn colors
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                chart: {
                    '1': 'hsl(var(--chart-1))',
                    '2': 'hsl(var(--chart-2))',
                    '3': 'hsl(var(--chart-3))',
                    '4': 'hsl(var(--chart-4))',
                    '5': 'hsl(var(--chart-5))'
                }
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)'
            },
            keyframes: {
                'accordion-down': {
                    from: { height: '0' },
                    to: { height: 'var(--radix-accordion-content-height)' }
                },
                'accordion-up': {
                    from: { height: 'var(--radix-accordion-content-height)' },
                    to: { height: '0' }
                },
                'gold-glow': {
                    '0%, 100%': { boxShadow: '0 0 15px rgba(253,185,49,0.4)' },
                    '50%': { boxShadow: '0 0 25px rgba(253,185,49,0.6)' }
                },
                'float': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' }
                }
            },
            animation: {
                'accordion-down': 'accordion-down 0.2s ease-out',
                'accordion-up': 'accordion-up 0.2s ease-out',
                'gold-glow': 'gold-glow 2s ease-in-out infinite',
                'float': 'float 3s ease-in-out infinite'
            },
            boxShadow: {
                'glow': '0 0 20px rgba(124,58,237,0.3)',
                'gold-glow': '0 0 15px rgba(253,185,49,0.4)',
            }
        }
    },
    plugins: [require("tailwindcss-animate")],
};
