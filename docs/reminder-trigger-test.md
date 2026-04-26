# Reminder Trigger Manual Test

1. Start the dev app with `npm run dev`.
2. Create or edit a mission.
3. Enable the reminder schedule and use `+1m`, or choose a time one minute from now.
4. Save the mission and keep the Electron app open.
5. Wait for the reminder time to pass.
6. Verify the fullscreen alarm opens.
7. Verify the PC/system sound repeats until you choose an alert action.

The real reminder path polls `http://127.0.0.1:8000/api/reminders/due`.
