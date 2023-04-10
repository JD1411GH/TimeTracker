# import modules
try :
    import os
    import configparser
    import time as tm
    from datetime import *
    import json
    import prettytable 
    import easygui
    import threading
except :
    myassert( False, "Could not import some modules. Use \'pip install <module>\' to install them", True )

# import internal modules
from Menu import *
from Utils import *

# reading config and database files globally, as its required for all functions
config = configparser.ConfigParser()
config.read('config.ini')
dbfile = open( config['DEFAULT']['TIMEDB'], 'r' )
timedb = json.loads( dbfile.read() )
dbfile.close()    

# Global variables
th_sed = None
stop_sed = False

# write to database file
def savedb() :
    file = open( config['DEFAULT']['TIMEDB'], 'w' )
    file.write( json.dumps(timedb, indent=4) )
    file.close()

# display the current statistics
def show_stats(wk=None) :
    global config
    global timedb

    # prepare table for current week data
    table = prettytable.PrettyTable(["Date", "Day", "Work Day", "Duration"])
    if wk is None :
        ( _, curweek, _) = datetime.today().isocalendar()
    else :
        curweek = wk

    # calculate deficit hours
    ndays = 0
    acttd = timedelta(0)
    flgTimerStarted = False
    for entry in timedb :
        # calculate number of working days
        ndays += entry['workday']

        # calculate total
        td = timedelta(0)
        for tim in entry['timestamps'] :
            (h, m, s) = tim['start'].split(":")
            start = datetime.combine(date.today(), time(int(h),int(m),int(s)))
            if tim['end'] is not None :
                (h, m, s) = tim['end'].split(":")
                end = datetime.combine(date.today(), time(int(h),int(m),int(s)))
                td += (end - start)
            else :
                flgTimerStarted = True
                end = datetime.today()
                td += (end - start)
        acttd = acttd + td + timedelta( minutes = entry['correction'] )

        # collect data for current week
        (y, mm, s) = entry['date'].split("-")
        dat = datetime( int(y), int(mm), int(s) )
        ( _, week, _) = dat.isocalendar()
        if week == curweek :
            hrs = td.seconds/3600
            hrs += ( int(entry['correction']) / 60 )
            table.add_row( [ entry['date'], dat.strftime("%a"), entry['workday'], f"{hrs:.2f}" ] )

    exphrs = ( ndays * float( config['DEFAULT']['DAILYEFFORT'] ) ) + float( config['DEFAULT']['CARRYDEFICIT'] )
    acthrs = acttd.total_seconds()/3600
    defhrs = exphrs - acthrs
    clearscr()
    print(table)
    print(f"Deficit hours: {defhrs:.2f}")
    print(f"Timer running: {flgTimerStarted}")

def start_timer() :
    global config
    global timedb

    # modify contents
    tod = datetime.today().strftime("%Y-%m-%d")
    idx = None
    flgTimerStarted = False
    for i in range( len(timedb) ) :
        if tod == timedb[i]['date'] :
            idx = i
            # Check if timer is already started
            for timestamp in timedb[i]['timestamps'] :
                if timestamp['start'] is not None and timestamp['end'] is None :
                    flgTimerStarted = True
                    break
            break
    if idx is None :
        datentry =     {
            "date": tod,
            "workday": 1,
            "timestamps": [],
            "correction" : 0
        }
        idx = len(timedb)
        timedb.append(datentry)
    if not flgTimerStarted :
        timentry = {
            "start": datetime.now().strftime("%H:%M:%S"),
            "end": None
            }
        timedb[idx]['timestamps'].append(timentry)
    
    # start sedentary timer if not started
    global th_sed
    if not th_sed.is_alive() :
        print( "Timer is not running" )
        th_sed = threading.Thread( target=sed_timer, daemon=True )
        global stop_sed
        stop_sed = False
        th_sed.start()

    # write back
    savedb()
    show_menu()

def stop_timer() :
    global config
    global timedb

    # modify contents
    tod = datetime.today().strftime("%Y-%m-%d")
    for i in range( len(timedb) ) :
        if tod == timedb[i]['date'] :
            for j in range( len(timedb[i]['timestamps']) ) :
                if timedb[i]['timestamps'][j]['end'] is None :
                    timedb[i]['timestamps'][j]['end'] = datetime.now().strftime("%H:%M:%S")
                    break
            break
    
    # stop sedentary timer
    global stop_sed
    stop_sed = True

    # write back
    savedb()
    show_menu()

def add_correction() :
    global config
    global timedb

    cor = input( "Enter mins to add: " )
    tod = datetime.today().strftime("%Y-%m-%d")
    for i in range( len(timedb) ) :
        if tod == timedb[i]['date'] :
            timedb[i]['correction'] += int(cor)
    savedb()
    show_menu()

def mark_day() :
    global config
    global timedb
    
    # find entry to modify
    curweek = datetime.today().strftime("%W")
    menu = Menu(show_stats)
    for i in range( len(timedb) ) :
        dat = date.fromisoformat( timedb[i]['date'] )
        week = dat.strftime("%W")
        if(week == curweek) :
            menu.add( MenuItem( timedb[i]['date'] ) )
    idx = menu.show()

    # get new value and write
    val = float( input( "Enter new value (0, 0.5, 1) : ") )
    for i in range( len(timedb) ) :
        if menu.getstr(idx-1) == timedb[i]['date'] :
            timedb[i]['workday'] = val

    # save and show menu
    savedb()
    show_menu()

def show_prev_stats() :
    global config
    global timedb

    menu = Menu(show_menu)
    menu.add( MenuItem("Prev") )
    menu.add( MenuItem("Next") )

    week = int( datetime.today().strftime("%W") ) - 1
    while( week > 0 ) :
        show_stats(week)
        ret = menu.show()
        if ret == 1 :
            week -= 1
        elif ret == 2 :
            week += 1

def show_menu() :
    show_stats()
    menu = Menu()
    menu.add( MenuItem( "Start Timer", start_timer ) )
    menu.add( MenuItem( "Stop Timer", stop_timer ) )
    menu.add( MenuItem( "Refresh", show_menu ) )
    menu.add( MenuItem( "Time Correction", add_correction ) )
    menu.add( MenuItem( "Mark holiday / half day", mark_day ) )
    menu.add( MenuItem( "Show previous records", show_prev_stats ) )
    while True: menu.show()

def sed_timer() :
    init = int(config['DEFAULT']['SEDMINS'])
    eta = timedelta( minutes=init )
    while not stop_sed :
        tm.sleep(1)
        eta -= timedelta(seconds=1)
        if eta.total_seconds() <= 0 :
            easygui.msgbox( "Time to take a walk" )
            eta = timedelta( minutes=init )

def main() :
    th_main = threading.Thread( target=show_menu )
    th_main.start()

    global th_sed
    th_sed = threading.Thread( target=sed_timer, daemon=True )
    th_sed.start()

    th_main.join()

if __name__ == "__main__":
    try :
        main()
    except (SystemExit, KeyboardInterrupt) as e :
        pass
    except:
        myassert( False, "An exception has occurred.", True )            
