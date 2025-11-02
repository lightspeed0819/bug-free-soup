# bug-free-soup
### Introduction
A timetable generator for a school project designed to meet specific needs.
Generates timetables for classes 6 to 10 given staff and subject details

### Features
May (not?) reduce some manual work for teachers
Will definitely get us lots of marks

### Installation and Usage
1. Copy all the files into location of choice keeping directory structure intact.
2. Run main.py

__Note: You won't be able to use it because it requires initial teacher and subject data to be formatted into csv files you won't have. It doesn't ship with the repo because the real thing will expose sensitive info and a sample would anyway be too incoherent, abstruse, unintelligible and obscure.__

### Known Issues
1. Doesn't support one class having more than one subject at the same time since a class may consist of students who have opted for different electives...
2. Only produces output for a small predefined range of classes (i.e 6 to 10) and a predefined number of classes (i.e A to E)
3. Is totally user unfriendly. This needs a section of its own. There is no convenient
   - CUI, forget the GUI... Even we are not comfortable using it.
   - way to modify any working data without writing SQL.
   - way to view the output in a nice printable form. It comes out in a .csv file
   - way for you to get this thing to work (as previously mentioned)

### Future Plans
Fix known issues.
