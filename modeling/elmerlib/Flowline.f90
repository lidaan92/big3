!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

FUNCTION BedFromFile( Model, nodenumber) RESULT(zb) !
    USE types
	Use DefUtils
    implicit none
	TYPE(Model_t) :: Model
    Real(kind=dp) :: mindist,dist,zb,yearinsec,ratio
    Real(kind=dp),allocatable :: xbed(:),zbed(:)
    Real(kind=dp) :: x,y,z,xnew
    INTEGER :: nodenumber,minind,RB,i
    CHARACTER(LEN=MAX_NAME_LEN) :: SolverName = 'BedFromFile'
		
    LOGICAL :: FirstTimeBed=.true.
    LOGICAL :: found

    SAVE xbed,zbed,RB
    SAVE FirstTimeBed

    if (FirstTimeBed) then

    	FirstTimeBed=.False.

        ! Load bed
        Open(10,file='Inputs/roughbed.dat')
        Read(10,*) RB
        Allocate(xbed(RB),zbed(RB))
        Do i=1,RB
        	Read(10,*) xbed(i),zbed(i)
		End do
		Close(10)
    End if

    ! Get current position
    x = Model % Nodes % x (nodenumber)
    y = Model % Nodes % y (nodenumber)

	! Now find data closest to current position
   	found = .FALSE.		
	
	IF (x > xbed(RB)) THEN
		xnew = xbed(RB)
		mindist=10000
   	ELSE
   		xnew = x
   		mindist=10000
   	END IF 
   	
   	DO i=1,RB
      	dist=abs(xnew-xbed(i))
      	IF (dist<=mindist) THEN
            mindist=dist
            minind=i
            found = .true.
      	END IF
   	END DO
	
	! Linearly interpolate to current position
	IF (found) THEN
   		if (xbed(minind) >= xnew) then 
      		ratio=(xnew-xbed(minind))/(xbed(minind+1)-xbed(minind))
      		zb=(zbed(minind)+ratio*(zbed(minind+1)-zbed(minind)))
      	else 
      		ratio=(xnew-xbed(minind))/(xbed(minind)-(xbed(minind-1)))
      		zb=(zbed(minind)+ratio*(zbed(minind)-zbed(minind-1)))
      	endif
      	!print *,'Zb at',xnew,zb
	else
	    print *,'No bed at',xnew
		CALL FATAL(SolverName,'No bed found for above coordinates')
	end if	
	
    Return
End

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! Calculates the velocity at the inflow boundary in the flowline model, using 
!! the SIA approximation. Currently assumes a basal velocity of 60 m/a at inflow (may
!! want to change when everything else is fixed).
!!
!! LMK, UW, 09/10/2014
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Function Inflow (Model, nodenumber, dumy) RESULT(vel)
   	USE types
   	USE CoordinateSystems
   	USE SolverUtils
   	USE ElementDescription
   	USE DefUtils
   	IMPLICIT NONE
   	TYPE(Model_t) :: Model
   	TYPE(Solver_t), TARGET :: Solver
   	INTEGER :: nodenumber
   	REAL(KIND=dp) :: Mask
   	INTEGER :: DIM, R, i, ind
   	REAL(KIND=dp) :: x, y, vel, thick, mindist, dist, dumy
   	REAL(KIND=dp) :: xf, yf, df, zb, zs, dv, us, ub
   	
   	LOGICAL :: found
   	LOGICAL :: FirsttimeInflow=.True.
     
    ! Save data for future use    
   	SAVE FirsttimeInflow,dv,us,df,zb,zs
	
	! Load data
   	if (FirsttimeInflow) then

   		FirsttimeInflow=.False.
   	   	
   	   	! Read velocity file
   		OPEN(10,file="Inputs/velocity.dat")
 		Read(10,*) R
 		! Only need to read the first row for inflow
   		READ(10,*) dv, us
   		CLOSE(10)

   		! Read flowline so we can figure out thickness
   		OPEN(10,file="Inputs/flowline.dat")
   		Read(10,*) R
   		! Only need to read the first row for inflow
   		READ(10,*) df, xf, yf, zb, zs 
   		CLOSE(10)
   		
   	End if
   	
    ! Get current position
   	x=Model % Nodes % x (nodenumber)
   	y=Model % Nodes % y (nodenumber)
   
    ! Compute velocity according to an approximation to the SIA, assuming n=3
    thick=zs-zb
    ub=200.0_dp
    vel = ub + (1.0_dp - ((zs - y) / (thick))**4_dp) * (us-ub)
   	
   	Return 
End
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

FUNCTION LateralConvergence (Model, nodenumber, dumy) RESULT(MassLoad)
   	USE Types
   	USE DefUtils
   	IMPLICIT NONE
   	TYPE(Model_t) :: Model
   	TYPE(Solver_t), TARGET :: Solver
   	TYPE(Nodes_t) :: ElementNodes
   	TYPE(Variable_t), POINTER :: WeightVariable,VelocityVariable

   	INTEGER :: nodenumber, i, R, minind
   	INTEGER, POINTER :: WeightPerm(:), VelocityPerm(:)
   	
   	REAL(KIND=dp) :: x, y, velx
	REAL(KIND=dp), ALLOCATABLE :: xhw(:), hw(:), dwdx(:)
   	REAL(KIND=dp) :: dumy, MassLoad, weight, ratio, dist, mindist, width, dw
   	REAL(KIND=dp), POINTER :: WeightValues(:), VelocityValues(:)
   	
   	LOGICAL :: FirstTimeLC = .TRUE.
   	LOGICAL :: found = .FALSE.
	
	! Save inputs from file for future use
	SAVE xhw, hw, dwdx, FirstTimeLC
	
	if (FirstTimeLC) then

    	FirsttimeLC=.False.

        ! Load data
        Open(10,file='Inputs/width.dat')
        Read(10,*) R
        Allocate(xhw(R),hw(R),dwdx(R))
        Do i=1,R
        	Read(10,*) xhw(i),hw(i),dwdx(i)
		End do
		Close(10)
    End if
	
	! Get current location
	x = Model % Nodes % x (nodenumber) 
	y = Model % Nodes % y (nodenumber)
	
	! Get element areas
	WeightVariable => VariableGet( Model % Variables, 'Flow Solution Weights' )
	IF (ASSOCIATED(WeightVariable)) THEN
    	WeightPerm    => WeightVariable % Perm
    	WeightValues  => WeightVariable % Values
    ELSE
        CALL FATAL('LateralConvergence','Could not find variable Weights. You need to add the Calculate Weights option.')
	END IF
	
	! Get velocity
	VelocityVariable => VariableGet( Model % Variables, 'Velocity 1' )
	IF (ASSOCIATED(VelocityVariable)) THEN
    	VelocityPerm    => VelocityVariable % Perm
    	VelocityValues  => VelocityVariable % Values
    ELSE
        CALL FATAL('LateralConvergence','Could not find x-velocity.')
	END IF
	
	! Get width at that location
	mindist=10000
   	DO i=1,SIZE(xhw)
      	dist=dabs(xhw(i)-x)
      	IF (dist<=mindist) THEN
        mindist=dist
        minind=i
        found = .true.
      	END IF
   	END DO

	! Interpolate width to current position
   	if (.not.found) then
      	print *, 'LateralConvergence: Could not find a suitable width to interpolate ',x
   	else
   		if (xhw(minind) >= x) then 
      		ratio=(x-xhw(minind))/(xhw(minind+1)-xhw(minind))
      		width=(hw(minind)+ratio*(hw(minind+1)-hw(minind)))
      		dw=(dwdx(minind)+ratio*(dwdx(minind+1)-dwdx(minind)))
      	else 
      		ratio=(x-xhw(minind))/(xhw(minind)-(xhw(minind-1)))
      		width=(hw(minind)+ratio*(hw(minind)-hw(minind-1)))
      		dw=(dwdx(minind)+ratio*(dwdx(minind)-dwdx(minind-1)))
      	endif
   	endif
	
	! Get weight and current velocity
	weight = WeightValues(WeightPerm(nodenumber))
	velx = VelocityValues(VelocityPerm(nodenumber))
	
	! Calculate mass load
	MassLoad = (-dw/width)*weight*velx	

	RETURN
END
FUNCTION LateralFrictionCoefficient( Model, nodenumber, dumy) RESULT(kcoeff) !
    USE types
	Use DefUtils
    implicit none
	TYPE(Model_t) :: Model
    Real(kind=dp) :: kcoeff, halfwidth, eta, dumy
    Real(kind=dp),allocatable :: xwidths(:),widths(:),junk(:)
    Real(kind=dp) :: x,y,mindist,dist,ratio,n,yearinsec,rhoi
    INTEGER :: nodenumber,minind,R,i
    TYPE(Variable_t), POINTER :: ViscosityVariable
    INTEGER, POINTER :: ViscosityPerm(:)
  	REAL(KIND=dp), POINTER :: ViscosityValues(:)
		
    LOGICAL :: FirsttimeLFC=.true.
    LOGICAL :: found

    SAVE xwidths, widths
    SAVE FirsttimeLFC
	
	if (FirsttimeLFC) then

    	FirsttimeLFC=.False.

        ! open file
        Open(10,file='Inputs/width.dat')
        Read(10,*) R
        Allocate(xwidths(R),widths(R),junk(R))
        Do i=1,R
        	Read(10,*) xwidths(i),widths(i),junk(i)
		End do
		Close(10)
    End if
    
    
    ! Find current x coordinate
    x = Model % Nodes % x (nodenumber)  
    
    ! Now find data closest to current position
   	found = .FALSE.		
	
   	mindist=100000
   	DO i=1,SIZE(xwidths)
      	dist=dabs(xwidths(i)-x)
      	IF (dist<=mindist) THEN
        mindist=dist
        minind=i
        found = .true.
      	END IF
   	END DO

	! Interpolate width to current position, and then find halfwidth for 
	! friction coefficient calculation
   	if (.not.found) then
      	print *, 'LateralFrictionCoefficient: Could not find a suitable width to interpolate ',x
   	else
   		if (xwidths(minind) >= x) then 
      		ratio=(x-xwidths(minind))/(xwidths(minind+1)-xwidths(minind))
      		halfwidth=(widths(minind)+ratio*(widths(minind+1)-widths(minind)))/2
      	else 
      		ratio=(x-xwidths(minind))/(xwidths(minind)-(xwidths(minind-1)))
      		halfwidth=(widths(minind)+ratio*(widths(minind)-widths(minind-1)))/2
      	endif
   	endif
    
	
	! Get viscosity at location
	ViscosityVariable => VariableGet( Model % Variables, 'Viscosity' )
   	IF (ASSOCIATED(ViscosityVariable)) THEN
    	ViscosityPerm    => ViscosityVariable % Perm
    	ViscosityValues  => ViscosityVariable % Values
    ELSE
        CALL FATAL('LateralFrictionCoefficient','Could not find variable Viscosity')
  	END IF
  	
  	! Get viscosity and set up variables
  	eta = ViscosityValues(ViscosityPerm(nodenumber))
	n = 3
	yearinsec = 365.25*24*60*60
	rhoi = 917.0/(1.0e6*yearinsec**2)
	
	! Compute lateral friction coefficient according to Gagliardin et al, 2010
	kcoeff = eta * (n+1)**(1/n) / (halfwidth**(1+(1/n)))
    
    Return
End

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

FUNCTION USF_Init (Model, nodenumber) RESULT(vel)
   	USE types
    USE CoordinateSystems
   	USE SolverUtils
   	USE ElementDescription
   	USE DefUtils
   	IMPLICIT NONE
   	TYPE(Model_t) :: Model
   	TYPE(Solver_t), TARGET :: Solver
   	INTEGER :: nodenumber,ind, Rs, i
   	REAL(KIND=dp) :: x, dist, mindist, output, ratio, vel
   	REAL(KIND=dp), ALLOCATABLE :: xs(:), vs(:)
   	LOGICAL :: found
   
    LOGICAL :: FirsttimeInit=.True.
    
    ! Save variables for future use    
   	SAVE FirsttimeInit,xs,vs,Rs
   
    ! Load velocity data
   	if (FirsttimeInit) then
   		! Read file
   		FirsttimeInit=.False.
   		
   		OPEN(10,file="Inputs/velocity.dat")
   		Read(10,*) Rs
   		ALLOCATE(xs(Rs), vs(Rs))
   		READ(10,*)(xs(i), vs(i), i=1,Rs)
   		CLOSE(10)
   	End if
   
    ! Find current position
	x=Model % Nodes % x (nodenumber)
   
   	found = .false.
   	mindist=dabs(2*(xs(1)-xs(2)))
   
   	do 20, i=1,Rs
      	dist=dabs(x-xs(i))
      	if (dist<=mindist .and. xs(i)<=x) then
        	mindist=dist
        	ind=i
        	found = .true.
      	endif 
   	20 enddo

    ! Linearly interpolate to current position
   	if (.not.found) then
      	print *, 'Could not find a suitable velocity to interpolate ',x
   	else
      	ratio=(x-xs(ind))/(xs(ind+1)-xs(ind))
      	vel=vs(ind)+ratio*(vs(ind+1)-vs(ind))
   	endif
   
   	Return
End
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

FUNCTION Viscosity( Model, nodenumber) RESULT(eta) !
    USE types
	Use DefUtils
    implicit none
	TYPE(Model_t) :: Model
    Real(kind=dp) :: T,eta,Aval,yearinsec,mindist,dist
    Real(kind=dp),allocatable :: xA(:),yA(:),A(:),TA(:)
    Real(kind=dp) :: x,y,z,xnew
    INTEGER :: nodenumber,minind,RA,i
    CHARACTER(LEN=MAX_NAME_LEN) :: SolverName = 'Viscosity'
		
    LOGICAL :: Firsttime5=.true.
    LOGICAL :: found
     
    ! Save values for future use
    SAVE xA,yA,A,RA,TA
    SAVE Firsttime5

    if (Firsttime5) then

    	Firsttime5=.False.

        ! open file
        Open(10,file='Inputs/flowparameters.dat')
        Read(10,*) RA
        Allocate(xA(RA),yA(RA),TA(RA),A(RA))
        Do i=1,RA
        	Read(10,*) xA(i),yA(i),TA(i),A(i)
		End do
		Close(10)
    End if

    ! Get position
    x = Model % Nodes % x (nodenumber)
    y = Model % Nodes % y (nodenumber)

	! Now find data closest to current position
   	found = .FALSE.		
	
	IF (x > xA(RA)) THEN
		xnew = XA(RA)
		mindist=10000
   	ELSE
   		xnew = x
   		mindist=5000
   	END IF 
   	
   	DO i=1,RA
      	dist=sqrt((xnew-xA(i))**2+(y-yA(i))**2)
      	IF (dist<=mindist) THEN
        mindist=dist
        minind=i
        found = .true.
      	END IF
   	END DO
	
	! Linearly interpolate to the current position
	IF (found) THEN
		yearinsec=365.25*24*60*60
    	Aval=A(minind)
		eta=(2.0*Aval*yearinsec)**(-1.0_dp/3.0_dp)*1.0e-6
	else
		print *,'No viscosity at',x,y
		CALL FATAL(SolverName,'No viscosity found for above coordinates')
	end if	

    Return
End

