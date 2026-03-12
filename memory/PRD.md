# King Klub - Product Requirements Document

## Overview
King Klub is a loyalty, engagement, and entertainment platform for King Karaoke. It encourages participation, rewards customers, and enhances the karaoke experience through gamification.

## Original Problem Statement
A full-stack web app for King Karaoke featuring:
- User Accounts & Profiles with rank tracking
- Reward System with 6 ranks (Peasant → Prince/Princess)
- Song Queue & Management
- Gamification & Accomplishments with badges
- Admin Tools for staff

## User Choices
- **Theme**: Royal purple (#0F0518) and gold (#FFD700) color scheme
- **Authentication**: JWT-based email/password
- **Admin Access**: Role-based (integrated with main app)

## User Personas
1. **Karaoke Patron**: Fun-loving singer who wants to track progress and earn rewards
2. **Regular Performer**: Competitive user aiming to climb leaderboard
3. **Staff/Admin**: Venue employee managing queue and awarding points

## Core Requirements
| Requirement | Status | Priority |
|-------------|--------|----------|
| User Registration/Login | ✅ Complete | P0 |
| Dashboard with Rank Display | ✅ Complete | P0 |
| Song Queue System | ✅ Complete | P0 |
| Points & Rewards | ✅ Complete | P0 |
| Leaderboard | ✅ Complete | P0 |
| Badges/Accomplishments | ✅ Complete | P1 |
| Admin Panel | ✅ Complete | P1 |

## What's Been Implemented (December 2025)

### Backend (FastAPI + MongoDB)
- User authentication (register, login, JWT tokens)
- Rank system (Peasant → Squire → Knight → Count → Duke → Prince)
- Song queue management (add, remove, position tracking)
- Points & badges system with automatic badge unlocking
- Leaderboard API
- Admin endpoints (queue management, user management, points adjustment)
- **QR Code Check-in System** - Daily venue check-ins with rotating QR codes
- **Battle/Challenge System** - 5 challenge types (Royal Duel, Blind Challenge, Rank Battle, Song Roulette, Harmony Duel)
- **Real-time WebSocket Voting** - Broadcast voting events to all connected clients
- Voting finalization with automatic winner determination and point awards

### Frontend (React + Tailwind)
- Landing page with royal theme
- Auth pages (login, register, separate admin login)
- Dashboard with rank card, progress bar, stats
- Song Queue page with add/remove functionality
- Leaderboard with top 3 podium display
- Badges/Accomplishments page
- Admin panel (queue management, user management, battle management)
- **Battle Arena Page** - Challenge opponents, view active battles
- **Real-time Vote Popup** - WebSocket-driven popup with countdown timer
- **Sound Effects** - Web Audio API sounds for battle start, voting, warnings, and victory

### Design
- Dark royal theme (#0F0518 background)
- Gold accents (#FFD700)
- Cinzel font for headings
- Manrope font for body text
- Glassmorphism cards with subtle borders
- Framer Motion animations

## Prioritized Backlog

### P0 - Critical (Completed)
- [x] User authentication
- [x] Core dashboard
- [x] Song queue
- [x] Basic points system

### P1 - Important (Completed)
- [x] Leaderboard
- [x] Badges system (16 badges across 5 categories)
- [x] Admin panel
- [x] Rank progression display
- [x] QR code check-in system
- [x] Battle/Challenge system with 5 modes
- [x] Real-time WebSocket voting
- [x] Sound effects for voting notifications

### P2 - Nice to Have (Future)
- [ ] Push notifications (mobile/browser)
- [ ] Email reminders for events
- [ ] Event management system
- [ ] Reward redemption system (free songs, merch)
- [ ] Song catalog/search integration
- [ ] Mobile app version

## Next Tasks
1. Expand notifications system (push/email)
2. Build reward redemption catalog
3. Create event management for special karaoke nights
4. Refactor server.py into modular routers

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Framer Motion, Shadcn/UI
- **Backend**: FastAPI, Motor (MongoDB async driver)
- **Database**: MongoDB
- **Auth**: JWT with bcrypt password hashing
