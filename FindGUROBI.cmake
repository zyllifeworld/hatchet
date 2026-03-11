# Simply provide the home of gurobi within the double apices here below
# REQUIREMENT 1: Full path to Gurobi's home which must have a name similar to "gurobiXXX" where XXX is the version.
# REQUIREMENT 2: Gurobi's must contain either (1) `lib` and `include` directories, (2) a folder named either `linux64` or `mac64` which correspondingly contains `lib` and `include` directories

set(GUROBI_HOME "" CACHE STRING "Path where Gurobi is installed")



if(EXISTS ${GUROBI_HOME} )
    message( "-- Gurobi's home is set to: " ${GUROBI_HOME} )

    # Detect Gurobi version and compute the library suffix.
    # Format A (<=9.x):  3 compact digits (e.g. gurobi902)
    #   -> lib suffix = first 2 digits ("90" -> libgurobi90.so)
    # Format B (>=10.x): 4 compact digits (e.g. gurobi1203 for 12.0.3)
    #   -> lib suffix = first 3 digits ("120" -> libgurobi120.so)
    # Format C (>=10.x): dotted version in path (e.g. gurobi11.0.3)
    #   -> lib suffix = MAJOR*10+MINOR (110 -> libgurobi110.so)
    string( REGEX MATCH "gurobi([0-9][0-9][0-9])[^0-9.]" _FMT_A_MATCH "${GUROBI_HOME}/" )
    string( REGEX MATCH "gurobi([0-9][0-9][0-9][0-9])[^0-9.]" _FMT_B_MATCH "${GUROBI_HOME}/" )
    string( REGEX MATCH "gurobi([0-9]+)\\.([0-9]+)\\." _FMT_C_MATCH "${GUROBI_HOME}" )

    if( _FMT_A_MATCH )
        string( REGEX REPLACE ".*gurobi([0-9][0-9][0-9])[^0-9.].*" "\\1" GUROBI_VER "${GUROBI_HOME}/" )
        string( STRIP "${GUROBI_VER}" GUROBI_VER )
        message( "-- The retrieved version of Gurobi is: " ${GUROBI_VER} )
        string( SUBSTRING "${GUROBI_VER}" 0 2 GUROBI_VER_LIB )
    elseif( _FMT_B_MATCH )
        string( REGEX REPLACE ".*gurobi([0-9][0-9][0-9][0-9])[^0-9.].*" "\\1" GUROBI_VER "${GUROBI_HOME}/" )
        string( STRIP "${GUROBI_VER}" GUROBI_VER )
        message( "-- The retrieved version of Gurobi is: " ${GUROBI_VER} )
        string( SUBSTRING "${GUROBI_VER}" 0 3 GUROBI_VER_LIB )
    elseif( _FMT_C_MATCH )
        string( REGEX REPLACE ".*gurobi([0-9]+)\\.([0-9]+)\\..*" "\\1" _GUROBI_MAJOR "${GUROBI_HOME}" )
        string( REGEX REPLACE ".*gurobi([0-9]+)\\.([0-9]+)\\..*" "\\2" _GUROBI_MINOR "${GUROBI_HOME}" )
        math( EXPR GUROBI_VER_LIB "${_GUROBI_MAJOR} * 10 + ${_GUROBI_MINOR}" )
        message( "-- The retrieved version of Gurobi is: ${_GUROBI_MAJOR}.${_GUROBI_MINOR} (lib suffix: ${GUROBI_VER_LIB})" )
    else()
        message( FATAL_ERROR "Cannot determine Gurobi version from GUROBI_HOME: ${GUROBI_HOME}" )
    endif()

    message( "-- The retrieved name of version-specific library is gurobi" ${GUROBI_VER_LIB} )

    file( GLOB GUROBI_LIB_FILE ${GUROBI_HOME}/linux64/lib/libgurobi${GUROBI_VER_LIB}.* )
    if( GUROBI_LIB_FILE )
    	message( "-- Gurobi library " ${GUROBI_LIB_FILE} " found in " ${GUROBI_HOME} "/linux64/lib/" )
    else()
	file( GLOB GUROBI_LIB_FILE ${GUROBI_HOME}/mac64/lib/libgurobi${GUROBI_VER_LIB}.* )
	if( GUROBI_LIB_FILE )
    	    message( "-- Gurobi library " ${GUROBI_LIB_FILE} " found in " ${GUROBI_HOME} "/mac64/lib/" )
    	else()
	    file( GLOB GUROBI_LIB_FILE ${GUROBI_HOME}/lib/libgurobi${GUROBI_VER_LIB}.* )
	    if( GUROBI_LIB_FILE )
    	    	message( "-- Gurobi library " ${GUROBI_LIB_FILE} " found in " ${GUROBI_HOME} "/lib/" )
	    else()
	        message( FATAL_ERROR "libgurobi" ${GUROBI_VER_LIB} ".* not found either in " ${GUROBI_HOME} "/linux64/lib/ or " ${GUROBI_HOME} "/mac64/lib/ or " ${GUROBI_HOME} "/lib, please check the file exists and provide the correct PATH or manually set Gurobi's version. CMake will exit." )
	    endif()
	endif()
    endif()

endif()

FIND_PATH(GUROBI_INCLUDE_DIR
          NAMES "gurobi_c++.h" "gurobi_c.h"
          PATHS /usr/local/gurobi751/linux64/include/ /Library/gurobi751/mac64/include/ ${GUROBI_HOME}/linux64/include/ ${GUROBI_HOME}/mac64/include/ ${GUROBI_HOME}/include/
          DOC "Gurobi include directory")

FIND_LIBRARY(GUROBI_CPP_LIB
             NAMES gurobi_c++
             PATHS /usr/local/gurobi751/linux64/lib/ /Library/gurobi751/mac64/lib/ ${GUROBI_HOME}/linux64/lib/ ${GUROBI_HOME}/mac64/lib/ ${GUROBI_HOME}/lib/
             DOC "Gurobi C++ Libraries")

FIND_LIBRARY(GUROBI_LIB
             NAMES "gurobi${GUROBI_VER_LIB}"
             PATHS /usr/local/gurobi751/linux64/lib/ /Library/gurobi751/mac64/lib/ ${GUROBI_HOME}/linux64/lib/ ${GUROBI_HOME}/mac64/lib/ ${GUROBI_HOME}/lib/
             DOC "Gurobi C Libraries")

set(GUROBI_LIBRARIES ${GUROBI_CPP_LIB} ${GUROBI_LIB})

set(GUROBI_FOUND TRUE)
