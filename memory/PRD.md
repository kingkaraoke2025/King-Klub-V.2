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
- **Title Preference**: Users can choose male (Squire/Knight/Count/Duke/Prince) or female (Lady/Dame/Countess/Duchess/Princess) rank titles

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
| Title Preference (Male/Female ranks) | ✅ Complete | P1 |
| QR Code Check-in System | ✅ Complete | P1 |
| Battle/Challenge System | ✅ Complete | P1 |
| Real-time WebSocket Voting | ✅ Complete | P1 |
| Sound Effects for Voting | ✅ Complete | P1 |
| Referral System | ✅ Complete | P1 |
| Queue Jump Perks | ✅ Complete | P1 |
| 5 Songs per 30-min Window | ✅ Complete | P1 |
| Admin Queue Reordering | ✅ Complete | P1 |

## What's Been Implemented

### December 2025 - Latest Updates
- **Admin Queue Reordering**: Admins can now manually move songs up/down in the queue
  - **Drag-and-drop**: Grab the grip handle (⋮⋮) and drag songs to any position
  - Up/down arrow buttons for quick single-position moves
  - Songs that used a perk to enter top 4 positions are "frozen" and cannot be moved
  - Visual indicator (lock icon + "Perk Used" badge) for protected songs
  - POST /api/admin/queue/{item_id}/reorder endpoint for drag-and-drop

- **5 Songs per 30-Minute Window**: Checked-in users can add up to 5 songs per 30-minute rolling window
  - Window resets every 30 minutes from check-in time
  - Clear feedback on songs remaining and time until reset
  - Backend validation with helpful error messages
  - GET /api/queue/my-status endpoint provides full queue eligibility info

### Previous Implementations

#### Backend (FastAPI + MongoDB)
- User authentication (register, login, JWT tokens)
- Rank system with male/female title options:
  - Peasant (both)
  - Squire / Lady
  - Knight / Dame
  - Count / Countess
  - Duke / Duchess
  - Prince / Princess
- Song queue management (add, remove, position tracking)
- Points & badges system with automatic badge unlocking (23 badges across 6 categories)
- Leaderboard API with title preference support
- Admin endpoints (queue management, user management, points adjustment)
- **QR Code Check-in System** - Daily venue check-ins with rotating QR codes
- **Battle/Challenge System** - 5 challenge types (Royal Duel, Blind Challenge, Rank Battle, Song Roulette, Harmony Duel)
- **Real-time WebSocket Voting** - Broadcast voting events to all connected clients
- **Referral System** - Users earn badges for referring friends
- **Rank-based Queue Perks** - Once-per-night queue jump based on rank

#### Frontend (React + Tailwind)
- Landing page with royal theme
- Auth pages (login, register, separate admin login)
- Dashboard with rank card, progress bar, stats, referral link sharing
- Song Queue page with add/remove functionality, perk usage
- Leaderboard with top 3 podium display
- Badges/Accomplishments page
- Admin panel (queue management, user management, battle management, delete users)
- **Battle Arena Page** - Challenge opponents, view active battles
- **Real-time Vote Popup** - WebSocket-driven popup with countdown timer
- **Sound Effects** - Web Audio API sounds for battle start, voting, warnings, and victory
- **How to Earn Points Page** - Detailed breakdown of all badges and point actions

### Design
- Dark royal theme (#0F0518 background)
- Gold accents (#FFD700)
- Cinzel font for headings
- Manrope font for body text
- Glassmorphism cards with subtle borders
- Framer Motion animations

## Prioritized Backlog

### P0 - Critical (All Completed)
- [x] User authentication
- [x] Core dashboard
- [x] Song queue
- [x] Basic points system

### P1 - Important (All Completed)
- [x] Leaderboard
- [x] Badges system (23 badges across 6 categories)
- [x] Admin panel
- [x] Rank progression display
- [x] QR code check-in system
- [x] Battle/Challenge system with 5 modes
- [x] Real-time WebSocket voting
- [x] Sound effects for voting notifications
- [x] Referral system with badges
- [x] Queue jump perks based on rank
- [x] 5 songs per 30-minute window feature

### P2 - Nice to Have (Future)
- [ ] Push notifications (mobile/browser)
- [ ] Email reminders for events
- [ ] Event management system
- [ ] Reward redemption system (free songs, merch)
- [ ] Song catalog/search integration
- [ ] Mobile app version

## Pending Issues
- User reported "uncaught runtime errors" after admin login (not reproduced - monitor for recurrence)

## Next Tasks
1. Monitor for any runtime errors reported by users
2. Expand notifications system (push/email)
3. Build reward redemption catalog
4. Create event management for special karaoke nights
5. Refactor server.py into modular routers (recommended for maintainability)

## Test Reports
- `/app/test_reports/iteration_1.json` - Battle system tests
- `/app/test_reports/iteration_3.json` - Queue song limit tests (33/33 passed)

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Framer Motion, Shadcn/UI
- **Backend**: FastAPI, Motor (MongoDB async driver)
- **Database**: MongoDB
- **Auth**: JWT with bcrypt password hashing
- **Timezone**: America/Chicago (hardcoded for venue)

## Test Credentials
- **Admin**: admin@kingkaraoke2025.com / admin123
- **User**: royaltest@example.com / password123
