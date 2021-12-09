""" Generate the information necessary to product the vrctst input files
"""

import os
import stat
import ioformat
import automol
import varecof_io
from autorun._run import run_script
from autorun._run import from_input_string
from autorun._script import SCRIPT_DCT


# Default names of input and output files
INPUT_NAME = 'tst.inp'
AUX_NAMES = (
    'structure.inp',
    'divsur.inp',
    'lr_divsur.inp',
    'molpro.inp',
    'run.tml',
    'mc_flux.inp',
    'convert.inp',
    'machines',
    'molpro.sh')
POT_INPUT_NAMES = (
    '{}_corr.f'
    'dummy_corr.f',
    'pot_aux.f',
    'makefile')

# Names of strings, files that go into the input
DUMMY_NAME = 'dummy_corr_'
LIB_NAME = 'libcorrpot.so'
EXE_NAME = 'molpro.sh'
SPC_NAME = 'run'
GEOM_PTT = 'GEOMETRY_HERE'
ENE_PTT = 'molpro_energy'

# Default nmaes of output
POT_OUTPUT_NAMES = (
    'libcorrpot.so',)

OUTPUT_NAMES = ('flux.out',)
DIVSUR_OUTPUT_NAMES1 = ('divsur.out',)

# Default dictionary of parameters for VRC-TST
VRC_DCT = {
    'fortran_compiler': 'gfortran',
    'base_name': 'run',
    'spc_name': 'run',
    'memory': 4.0,
    'r1dists_lr': [8., 6., 5., 4.5, 4.],
    'r1dists_sr': [4., 3.8, 3.6, 3.4, 3.2, 3., 2.8, 2.6, 2.4, 2.2],
    'r2dists_sr': [4., 3.8, 3.6, 3.4, 3.2, 3., 2.8, 2.6, 2.4, 2.2],
    'd1dists': [0.01, 0.5, 1.],
    'd2dists': [0.01, 0.5, 1.],
    'conditions': {},
    'nsamp_max': 2000,
    'nsamp_min': 50,
    'flux_err': 10,
    'pes_size': 2
}


# Specialized runners
def flux_file(varecof_script_str, mcflux_script_str,
              run_dir, input_strs_dct):
    """  Calculate the flux file
    """

    # Write all of the input strings
    for name, string in input_strs_dct.items():
        ioformat.pathtools.write_file(string, run_dir, name)

    # Convert the molpro.sh file into an executable
    molpro_sh_script = os.path.join(run_dir, 'molpro.sh')
    os.chmod(
        molpro_sh_script,
        mode=(os.stat(molpro_sh_script).st_mode |
              stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))

    # Make the scratch directory
    os.mkdir(os.path.join(run_dir, 'scratch'))

    # Run VaReCoF
    run_script(varecof_script_str, run_dir)

    print('Running', run_dir)

    # Generate and read the flux file for the return
    # print('Generating flux file with TS N(E) '
    #       'from VaReCoF output...')
    # run_script(mcflux_script_str, run_dir)

    # flux_str = ioformat.pathtools.read_file(run_dir, 'flux.dat')

    return flux_str


# Helpful runners for the more directly called ones
def compile_potentials(vrc_path, mep_distances, potentials,
                       bnd_frm_idxs, fortran_compiler,
                       dist_restrict_idxs=(),
                       pot_labels=(),
                       pot_file_names=(),
                       spc_name=SPC_NAME):
    """  use the MEP potentials to compile the correction potential .so file
    """

    # Change the coordinates of the MEP distances
    # mep_distances = [dist * phycon.BOHR2ANG for dist in mep_distances]
    bnd_frm_idxs = tuple(idx+1 for idx in bnd_frm_idxs)

    # Build string Fortan src file containing correction potentials
    species_corr_str = varecof_io.writer.corr_potentials.species(
        mep_distances,
        potentials,
        bnd_frm_idxs,
        dist_restrict_idxs=dist_restrict_idxs,
        pot_labels=pot_labels,
        species_name=spc_name)

    # Build string dummy corr file where no correction used
    dummy_corr_str = varecof_io.writer.corr_potentials.dummy()

    # Build string for auxiliary file needed for spline fitting
    pot_aux_str = varecof_io.writer.corr_potentials.auxiliary()

    # Build string for makefile to compile corr pot file into .so file
    makefile_str = varecof_io.writer.corr_potentials.makefile(
        fortran_compiler, pot_file_names=pot_file_names)

    # Write all of the files needed to build the correction potential
    ioformat.pathtools.write_file(
        species_corr_str, vrc_path, spc_name+'_corr.f')
    ioformat.pathtools.write_file(
        dummy_corr_str, vrc_path, 'dummy_corr.f')
    ioformat.pathtools.write_file(
        pot_aux_str, vrc_path, 'pot_aux.f')
    ioformat.pathtools.write_file(
        makefile_str, vrc_path, 'makefile')

    # Compile the correction potential
    varecof_io.writer.corr_potentials.compile_corr_pot(vrc_path)

    # Maybe read the potential and return it, prob not needed
    corr_pot_file_str = ioformat.pathtools.read_file(
        vrc_path, 'libcorrpot.so')

    return corr_pot_file_str


def frame_oriented_structure(script_str, run_dir,
                             divsur_inp_str,
                             struct_inp_str,
                             divsur_name='divsur.inp',
                             tst_name='tst.inp',
                             struct_name='structure.inp',
                             output_names=('divsur.out',)):
    """ get the divsur.out string containing divsur-frame geoms
    """

    # Fill in the submission script
    script_str.format(divsur_name, tst_name)

    # Write some boilerplate tst.inp string to run script
    tst_str = varecof_io.writer.input_file.tst(1, 1, .1, 1)

    # Put the tst string in the aux dct
    aux_dct = {tst_name: tst_str,
               struct_name: struct_inp_str}

    # Run the script to generate the divsur.out file
    output_strs = from_input_string(
        script_str, run_dir, divsur_inp_str,
        aux_dct=aux_dct,
        input_name=divsur_name,
        output_names=output_names)
    divsur_out_str = output_strs[0]

    # Read the geometries and facial symmetries from divsur out file
    if divsur_out_str is not None:
        geos = varecof_io.reader.divsur.frame_geometries(
            divsur_out_str)
        faces, faces_symm = varecof_io.writer.assess_face_symmetries(
            *geos)
    else:
        geos, faces, faces_symm = None, None, None

    return geos, faces, faces_symm


def write_input(run_dir,
                ref_zma, rct_zmas,
                npot, bnd_frm_keys,
                machine_dct, vrc_dct):
    """ prepare all the input files for a vrc-tst calculation
    """

    # Get the indices
    min_idx, max_idx = min(bnd_frm_keys), max(bnd_frm_keys)

    # Build geometries needed for the varecof run
    tot_geo, isol_fgeos, a1_idxs = varecof_io.writer.fragment_geometries(
        ref_zma, rct_zmas, (min_idx, max_idx))

    frames, npivots = varecof_io.writer.build_pivot_frames(
        isol_fgeos, a1_idxs)
    pivot_angles = varecof_io.writer.calc_pivot_angles(
        isol_fgeos, frames)
    pivot_xyzs = varecof_io.writer.calc_pivot_xyzs(
        tot_geo, isol_fgeos, (min_idx, max_idx))

    # Write the long- and short-range divsur input files
    lrdivsur_inp_str = varecof_io.writer.input_file.divsur(
        vrc_dct['r1dists_lr'], 1, 1, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0])

    # Write the short-range divsur files
    d1dists, d2dists = vrc_dct['d1dists'], vrc_dct['d2dists']
    t1angs = [pivot_angles[0]] if pivot_angles[0] is not None else []
    t2angs = [pivot_angles[1]] if pivot_angles[1] is not None else []
    if automol.geom.is_atom(isol_fgeos[0]):
        d1dists = []
        t1angs = []
    if automol.geom.is_atom(isol_fgeos[1]):
        d2dists = []
        t2angs = []
    if automol.geom.is_linear(isol_fgeos[0]):
        d1dists = [0.]
        t1angs = []
    if automol.geom.is_linear(isol_fgeos[1]):
        d2dists = [0.]
        t2angs = []
    if all(npiv > 1 for npiv in npivots):
        r2dists = vrc_dct['r2dists_sr']
    else:
        r2dists = []
        print('no r2dist')

    srdivsur_inp_str = varecof_io.writer.input_file.divsur(
        vrc_dct['r1dists_sr'],
        npivots[0], npivots[1],
        pivot_xyzs[0], pivot_xyzs[1],
        frame1=frames[0], frame2=frames[1],
        d1dists=d1dists, d2dists=d2dists,
        t1angs=t1angs, t2angs=t2angs,
        r2dists=r2dists,
        **vrc_dct['conditions'])

    # Build the structure input file string
    struct_inp_str = varecof_io.writer.input_file.structure(
        isol_fgeos[0], isol_fgeos[1])

    # Obtain symmetries of the fragment molecules
    conv_script_str = SCRIPT_DCT['varecof_conv_struct']
    _, faces, faces_symm = frame_oriented_structure(
        conv_script_str, run_dir, srdivsur_inp_str, struct_inp_str)

    # Write the tst.inp file
    tst_inp_str = varecof_io.writer.input_file.tst(
        vrc_dct['nsamp_max'], vrc_dct['nsamp_min'],
        vrc_dct['flux_err'], vrc_dct['pes_size'],
        faces=faces, faces_symm=faces_symm)

    # Write the molpro executable and potential energy surface input string
    molpro_sh_script_str = SCRIPT_DCT['molpro2015'].format(1)
    els_inp_str = varecof_io.writer.input_file.elec_struct(
        run_dir, vrc_dct['base_name'], npot,
        dummy_name='dummy_corr_', lib_name='libcorrpot.so',
        exe_name='molpro.sh',
        geo_ptt='GEOMETRY_HERE', ene_ptt='molpro_energy')

    # Write the mc_flux.inp input string
    mc_flux_inp_str = varecof_io.writer.input_file.mc_flux()

    # Write the convert.inp input string
    conv_inp_str = varecof_io.writer.input_file.convert()

    # Write machines file to set compute nodes
    machine_file_str = varecof_io.writer.input_file.machinefile(machine_dct)

    # Collate the input strings and write the remaining files
    input_strs = (
        srdivsur_inp_str, lrdivsur_inp_str,
        tst_inp_str,
        els_inp_str, struct_inp_str,
        mc_flux_inp_str, conv_inp_str,
        machine_file_str, molpro_sh_script_str)
    input_names = (
        'divsur.inp', 'lr_divsur.inp',
        'tst.inp',
        'molpro.inp', 'structure.inp',
        'mc_flux.inp', 'convert.inp',
        'machines', 'molpro.sh')

    return dict(zip(input_names, input_strs))
