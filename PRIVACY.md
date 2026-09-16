# Privacy Policy for backlink-go

Last updated: September 16, 2026

## Overview

backlink-go is an open-source workflow that runs locally for an authorized user. Its Google integration creates and maintains a Google Sheets workbook and provides explicit, read-only Gmail search and single-message reading commands.

## Google data accessed

The application requests these Google OAuth scopes:

- `https://www.googleapis.com/auth/drive.file` to create and update the specific Google Sheets files used with the application.
- `https://www.googleapis.com/auth/gmail.readonly` to search and read Gmail messages when the user runs a Gmail command.

The application does not send email, modify messages, change labels, delete messages, or download file attachments.

## How data is used

Google Sheets data is used only to maintain the user's Backlink Operations records. Gmail data is used only to return the search results or message requested by the user. Gmail message content is transient command output and is not written to Google Sheets, repository files, evidence records, or analytics systems.

Google user data is not sold, used for advertising, or shared with third parties. Google processes API requests as the service provider for the user's account.

## Local storage and retention

OAuth client configuration, access tokens, refresh tokens, workbook configuration, and replacement backups are stored only in the user's ignored local `.backlink-go/runtime/` directory. On supported Unix systems the directory uses mode `0700` and private files use mode `0600`.

The user controls retention by deleting the local runtime directory, removing locally created backups, deleting the Google Sheets workbook, or revoking the application's access from their Google Account. Replacing credentials preserves a local backup so the user can recover from an interrupted account switch.

## Security

The application uses Google's installed desktop OAuth flow with a local loopback callback. Passwords, browser cookies, local storage, one-time codes, raw sessions, and downloaded Gmail attachments are not collected or stored by the application.

## Revoking access

Users can revoke backlink-go from the [Google Account connections page](https://myaccount.google.com/connections). After revocation, local token files can be removed from `.backlink-go/runtime/`.

## Contact

Questions about this policy can be raised through the repository's [GitHub issue tracker](https://github.com/ALHDLIOX/backlink_go/issues). Do not include credentials, tokens, private email content, or other sensitive information in a public issue.
