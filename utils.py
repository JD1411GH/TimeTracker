import os

# custom utility functions
def myassert(cond, msg, raise_excep = False) :
    if not cond :
        print( "ERROR: " + msg )
        if raise_excep :
            input("Press <enter> to see details.")
            raise
        else :
            input("Press <enter> to exit...")
            os.abort()

def mycls() :
    if os.name =='posix' :
        os.system('clear')
        pass
    elif os.name =='nt' :
        os.system('cls')
    else :
        pass
