from blinker import Namespace

hive_signals = Namespace()

user_logged_in = hive_signals.signal('user-logged-in')
user_registered = hive_signals.signal('user-registered')
course_enrolled = hive_signals.signal('course-enrolled')
fee_paid = hive_signals.signal('fee-paid')
announcement_posted = hive_signals.signal('announcement-posted')
timetable_updated = hive_signals.signal('timetable-updated')
