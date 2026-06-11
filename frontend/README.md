<!--
Purpose: Provide frontend development and run instructions for the Next.js app.
Used by: Frontend developers and contributors working on the UI.
Main dependencies: Next.js, npm packages, frontend environment variables, and backend API.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Frontend App

Frontend ini adalah dashboard Next.js untuk simulasi fraud detection retail app.

## Purpose

- Menjalankan simulasi new user dan existing user.
- Menampilkan hasil inference per stage.
- Menyediakan graph analytics dan chatbot tab.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

## Project Notes

- Backend API default: `http://localhost:8000`
- Inference endpoints live under `/api/inference/*`
- New-user registration uses the dedicated new-user model artifact
- Existing-user flow uses the legacy full-feature model

## Learn More

To learn more about Next.js, take a look at these resources:

- [Next.js Documentation](https://nextjs.org/docs)
- [Next.js Learn](https://nextjs.org/learn)

