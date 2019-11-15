# rsync Wrapper to Protect my Backup
Say I have two machines where one is my NAS and the other my off-site backup.
Most of my data is photos and documents I keep as an archive. Those basically
never change.

I could simply hard-code a script that runs rsync of the stuff I want to
backup. However, if there is a crypto virus lurking around it may even
corrupt my backup that way. This is what this tool is targeted against.

The basic idea is to check a measure for *difference* between my NAS and the
backup solely for files that *already exist on both sides*. If this
difference gets unrealistically high I'd rather not override the backup. New
files should be excluded as we don't care about their integrity here.

I already had a somewhat-working bash implementation of this but lost it due
to some NAS update hickup. So, right now, github ;-)

Disclaimer: Use to kill your own machines at your own risk. Review before you
run it. Don't come to me crying! License: Creative Commons.
