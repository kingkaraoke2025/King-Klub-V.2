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

## What's Been Implemented (March 2026)

### Backend (FastAPI + MongoDB)
- User authentication (register, login, JWT tokens)
- Rank system (Peasant → Squire → Knight → Count → Duke → Prince)
- Song queue management (add, remove, position tracking)
- Points & badges system with automatic badge unlocking
- Leaderboard API
- Admin endpoints (queue management, user management, points adjustment)

### Frontend (React + Tailwind)
- Landing page with royal theme
- Auth pages (login, register)
- Dashboard with rank card, progress bar, stats
- Song Queue page with add/remove functionality
- Leaderboard with top 3 podium display
- Badges/Accomplishments page
- Admin panel (queue management, user management)

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
- [x] Badges system
- [x] Admin panel
- [x] Rank progression display

### P2 - Nice to Have
- [ ] Real-time WebSocket updates for queue
- [ ] Push notifications
- [ ] Check-in feature for venue visits
- [ ] Battle mode (head-to-head competitions)
- [ ] Event management system
- [ ] Reward redemption system (free songs, merch)
- [ ] Song catalog/search integration
- [ ] QR code check-in

## Next Tasks
1. Add WebSocket for real-time queue updates
2. Implement check-in feature for venue visits (+50 pts)
3. Add battle/voting system for song performances
4. Build reward redemption catalog
5. Create event management for special karaoke nights

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Framer Motion, Shadcn/UI
- **Backend**: FastAPI, Motor (MongoDB async driver)
- **Database**: MongoDB
- **Auth**: JWT with bcrypt password hashing
