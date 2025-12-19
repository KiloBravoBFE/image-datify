# image-datify
This is a small tool grown from frustration, as copying images en masse (as you do...) sometimes breaks everything. And if you have 60k images on your phone, the last thing you want is having all of them show up as "taken today". 
What exactly your phone uses to determine the date apparently also depends from album to album, at least it does on my S25 Edge, but this might at least help in solving the problem.

Also: this was written / tested / used entirely on Linux. If you are using Windows or MacOS, it *might* work, so good luck.

And because of system limitations, it only seems to be possible to modify the "creation date" of a file on Windows, at least I haven't found another way to do it (or test it on Windows for that matter), but that could maybe work there. Again, I don't know, good luck with that.

And yes, I know the Interface still looks pretty bad, but it is what it is. It works.

Currently supported formats (still hardcoded, might add custom ones later, for the customisation ends with customising the code):

- Year-Month-Day at Hour.Minute.Second
- Year-Month-Day at Hour-Minute-Second
- Year-Month-Day-HourMinuteSecond
- YearMonthDay_HourMinuteSecond
- Year-Month-Day_Hour-Minute-Second


(You need the PyQt5 lib, so install it with your distro's Package Manager or with PIP) 
