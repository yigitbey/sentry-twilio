# sentry-twilio
A plugin for [Sentry](https://www.getsentry.com/) that sends SMS notifications via [Twilio](http://www.twilio.com/)

**Note**: Only works with US numbers, mostly because I'm too lazy to think about international phone numbers and what to do with them. Feel free to submit a pull request.

**Fork update**: Changed the phone validation regex, it should also work with International numbers now.


Sentry will automagically detect that it has been installed.

## Configuration
`sentry-twilio` needs 4 pieces of information to set this up correctly.

### Account SID & Auth Token
The Account SID and Auth Token can both be found on your [Twilio account dashboard](https://www.twilio.com/user/account).
![](http://i.imgur.com/Km3cI.png)

### SMS From # 
This is the number that was purchased through Twilio. [Twilio documentation for more information](https://www.twilio.com/help/faq/phone-numbers).

Examples:
```
+13305093095
// or
5551234567
```

### SMS To #'s
A list of phone numbers to send to separated by commas.

Example:
```
+12-455-4325522, 55-512-3456794
```
