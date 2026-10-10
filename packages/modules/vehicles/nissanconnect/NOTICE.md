# Third-party attribution

This openWB integration follows the repository's GNU GPL version 3 license.
The adapted MIT source retains the notice below; this file does not relicense
the complete module under MIT or grant access to Nissan services.

The MyNISSAN EU protocol and login flow in `src/api.py` are adapted from
[HomeAssistant-NissanConnect](https://github.com/dan-r/HomeAssistant-NissanConnect/tree/b0bafe9108d4574e243aa182324584dbc68369ad),
revision b0bafe9108d4574e243aa182324584dbc68369ad.
Its client credits @mitchellrj and @Tobiaswk and explicitly states that portions
were relicensed from Apache License, Version 2.0 with permission. We preserve
that upstream provenance statement and rely on the reference's published MIT
grant. The earlier kamereon-python client credits Richard Mitchell (2020);
dartnissanconnect credits Tobias Westergaard Kjeldsen (2021).

Adapted for openWB by wippofax, 2026-09-11 through 2026-10-10: standard-library
transport, bounded authentication and battery validation, passive queries,
retry/error handling, native module integration and synthetic tests. The
reference project is not responsible for these modifications.

The retained MIT notice below accompanies the adapted source. See the
[user information](docs/user-information.md) for the unresolved service-access
question; software licensing does not settle that question. Nissan and MyNISSAN are referenced
to identify compatibility; this is an independent, unofficial integration.

MIT License

Copyright (c) 2024 Daniel Raper

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
