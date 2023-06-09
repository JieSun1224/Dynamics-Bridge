import os
import json
import shutil
from pymatgen.io.vasp.inputs import Poscar

def replace_value_in_file(filename, tag, new_value):
    # Open the file and read all lines
    with open(filename, 'r') as file:
        lines = file.readlines()

    # Find the line containing the tag and replace the value
    for i, line in enumerate(lines):
        if tag in line:
            lines[i] = line.replace('XXX', str(new_value))

    # Write the modified content back to the file
    with open(filename, 'w') as file:
        file.writelines(lines)

# Read parameters from the config file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

expansion = config["expansion"]
first_nsw = config["first_nsw"]
first_tebeg = config["first_tebeg"]
first_teend = config["first_teend"]
interval = config["interval"]
folder_count = config["folder_count"]
command = config["command"]

# Print preparation information
print("Preparing POSCAR, INCAR, KPOINTS, POTCAR, run.sh")

# Read the original POSCAR file
poscar = Poscar.from_file("POSCAR")

expansion = config["expansion"]

# Supercell expansion
poscar.structure.make_supercell(expansion)

# Save the expanded POSCAR file
poscar.write_file("SPOSCAR")

cp_command = 'cp POSCAR POSCAR.orig'
os.system(cp_command)

cp_command2 = 'cp SPOSCAR POSCAR'
os.system(cp_command2)

# INCAR file content
incar_content = '''Global Parameters
ISTART =  1            (Read existing wavefunction; if there)
# ISPIN =  2           (Spin polarised DFT)
# ICHARG =  11         (Non-self-consistent: GGA/LDA band structures)
LREAL  = Auto          (Projection operators: automatic)
ALGO  = Very Fast
# ENCUT  =  520        (Cut-off energy for plane wave basis set, in eV)
PREC   =  middle       (Precision level)
LWAVE  = .TRUE.        (Write WAVECAR or not)
LCHARG = .TRUE.        (Write CHGCAR or not)
ADDGRID= .TRUE.        (Increase grid; helps GGA convergence)
# LVTOT  = .TRUE.      (Write total electrostatic potential into LOCPOT or not)
# LVHAR  = .TRUE.      (Write ionic + Hartree electrostatic potential into LOCPOT or not)
# NELECT =             (No. of electrons: charged cells; be careful)
# LPLANE = .TRUE.      (Real space distribution; supercells)
# NPAR   = 4           (Max is no. nodes; don't set for hybrids)
# NWRITE = 2           (Medium-level output)
# KPAR   = 2           (Divides k-grid into separate groups)
# NGX    = 500         (FFT grid mesh density for nice charge/potential plots)
# NGY    = 500         (FFT grid mesh density for nice charge/potential plots)
# NGZ    = 500         (FFT grid mesh density for nice charge/potential plots)

Electronic Relaxation
ISMEAR =  0
SIGMA  =  0.05
EDIFF  =  1E-04

Molecular Dynamics
IBRION =  0            (Activate MD)
NSW    =  XXX          (Max electronic SCF steps)
EDIFFG = -1E-02        (Ionic convergence; eV/AA)
POTIM  =  2            (Timestep in fs)
SMASS  =  0            (MD Algorithm: -3-microcanonical ensemble; 0-canonical ensemble)
TEBEG  =     XXX     (Start temperature K)
TEEND  =     XXX     (Start temperature K)
! MDALGO =  1          (Andersen Thermostat)
! ISYM   =  0          (Symmetry: 0=none; 2=GGA; 3=hybrids)

##opt86b_vdW
##  IVDW=11
LDAU=.TRUE.
LDAUTYPE=2
LDAUL=-1 2
LDAUU=0.0 3.5
LDAUJ=0.0 0.0
LMAXMIX=4

IVDW = 11'''

# KPOINTS file content
kpoints_content = '''Auto-mesh
0 
gamma
 1  1  1
 0  0  0'''

# Write INCAR file
incar_path = os.path.abspath('INCAR')
with open(incar_path, 'w') as incar_file:
    incar_file.write(incar_content)

# Write KPOINTS file
kpoints_path = os.path.abspath('KPOINTS')
with open(kpoints_path, 'w') as kpoints_file:
    kpoints_file.write(kpoints_content)

# Create folders
folder_names = [f"Folder{i}" for i in range(1, folder_count+1)]
for folder_name in folder_names:
    os.makedirs(folder_name, exist_ok=True)

# Copy files to each folder
files_to_copy = ['INCAR', 'KPOINTS', 'POTCAR', 'POSCAR', 'run.sh']
for folder_name in folder_names:
    for file in files_to_copy:
        shutil.copy(file, folder_name)

# Traverse folders and modify the NSW, TEBEG, and TEEND values in each folder's INCAR file
for i, folder_name in enumerate(folder_names):
    # Calculate the NSW, TEBEG, and TEEND values for the current folder
    current_nsw = first_nsw
    current_tebeg = first_tebeg + (i * interval)
    current_teend = first_teend + (i * interval)

    # Enter the folder
    os.chdir(folder_name)

    # Modify the INCAR file
    replace_value_in_file('INCAR', 'NSW', current_nsw)
    replace_value_in_file('INCAR', 'TEBEG', current_tebeg)
    replace_value_in_file('INCAR', 'TEEND', current_teend)

    # Exit the folder
    os.chdir('..')

# Execute the command
for folder_name in folder_names:
    os.chdir(folder_name)
    os.system(command)
    os.chdir('..')

print("All calculations finished.")
