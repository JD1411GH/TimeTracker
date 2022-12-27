# MenuItem class
class MenuItem :
    def __init__(this, txt, func=None) :
        this.Txt = txt	# data members are defined on the fly
        this.Func = func
        

# Menu class        
class Menu :         
    def __init__(this, exit_handler=None) :
        this.Itemlist = []
        this.ExitHandler = exit_handler
        
    def add(this, item) :
        this.Itemlist.append( item )

    def show(this) :
        entry = 1
        print("")
        for item in this.Itemlist :
            print( entry, item.Txt )
            entry += 1
        if this.ExitHandler is None :
            print( 0, "Exit" )
        else :
            print( 0, "Go back.." )
        choice = int( input("Please enter your choice: ") )
        assert choice <= len(this.Itemlist), "Invalid choice"
        if choice == 0 :
            if this.ExitHandler is None :
                exit(0)
            else :
                this.ExitHandler()
        else :
            if this.Itemlist[choice-1].Func is not None :
                this.Itemlist[choice-1].Func()
        return choice
            
    def getstr(self, itemidx) :
        return self.Itemlist[itemidx].Txt
