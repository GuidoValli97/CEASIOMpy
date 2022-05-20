"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/CPACS2GMSH/generategmesh.py'

Python version: >=3.7

| Author : Tony Govoni
| Creation: 2022-03-22

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import shutil
import sys
from pathlib import Path

import gmsh
import pytest
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.generategmesh import (
    ModelPart,
    generate_gmsh,
    get_entities_from_volume,
)
from cpacspy.cpacspy import CPACS

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH

MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(CPACS_FILES_PATH, "simpletest_cpacs.xml")
TEST_OUT_PATH = Path(MODULE_DIR, "ToolOutput")

# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def test_generate_gmsh():
    """
    This test try to generate a simple mesh and test if the SU2 markers
    are correctly assigned for simpletest_cpacs.xml

    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    generate_gmsh(
        CPACS_IN_PATH,
        TEST_OUT_PATH,
        TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=5,
        symmetry=False,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        refine_factor=1.0,
        auto_refine=False,
        testing_gmsh=False,
    )

    with open(Path(TEST_OUT_PATH, "mesh.su2"), "r") as f:
        content = f.read()

    # assert "NMARK= 4" in content
    assert "MARKER_TAG= Wing" in content
    assert "MARKER_TAG= Wing_mirrored" in content
    assert "MARKER_TAG= SimpleFuselage" in content
    assert "MARKER_TAG= Farfield" in content

    # Delete files generated by the test
    files_to_delete = [p for p in TEST_OUT_PATH.iterdir() if p.suffix in [".brep", ".su2"]]
    for file in files_to_delete:
        file.unlink()


def test_generate_gmsh_symm():
    """
    This test try to generate a simple symmetric mesh and test if the SU2 markers
    are correctly assigned for simpletest_cpacs.xml

    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    generate_gmsh(
        CPACS_IN_PATH,
        TEST_OUT_PATH,
        TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=5,
        symmetry=True,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        refine_factor=1.0,
        auto_refine=False,
        testing_gmsh=False,
    )

    with open(Path(TEST_OUT_PATH, "mesh.su2"), "r") as f:
        content = f.read()

    assert "MARKER_TAG= Wing" in content
    assert "MARKER_TAG= SimpleFuselage" in content
    assert "MARKER_TAG= Farfield" in content
    assert "MARKER_TAG= symmetry" in content

    # Delete files generated by the test
    files_to_delete = [p for p in TEST_OUT_PATH.iterdir() if p.suffix in [".brep", ".su2"]]
    for file in files_to_delete:
        file.unlink()


def test_symm_part_removed():
    """
    Test if when symmetry is used, symmetry part are removed

    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    generate_gmsh(
        CPACS_IN_PATH,
        TEST_OUT_PATH,
        TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=5,
        symmetry=True,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        refine_factor=1.0,
        auto_refine=False,
        testing_gmsh=False,
    )

    with open(Path(TEST_OUT_PATH, "mesh.su2"), "r") as f:
        content = f.read()

    # symmetric wing should be removed
    assert "MARKER_TAG= Wing_mirrored" not in content

    # Delete files generated by the test
    files_to_delete = [p for p in TEST_OUT_PATH.iterdir() if p.suffix in [".brep", ".su2"]]
    for file in files_to_delete:
        file.unlink()


def test_get_entities_from_volume():
    """
    Test on a simple cube if the lower dimensions entities are correctly found.

    """
    gmsh.initialize()
    test_cube = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    gmsh.model.occ.synchronize()
    surfaces_dimtags, lines_dimtags, points_dimtags = get_entities_from_volume([(3, test_cube)])
    assert len(surfaces_dimtags) == 6
    assert len(lines_dimtags) == 12
    assert len(points_dimtags) == 8
    assert surfaces_dimtags == [(2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6)]
    assert lines_dimtags == [
        (1, 1),
        (1, 2),
        (1, 3),
        (1, 4),
        (1, 5),
        (1, 6),
        (1, 7),
        (1, 8),
        (1, 9),
        (1, 10),
        (1, 11),
        (1, 12),
    ]
    assert points_dimtags == [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8)]
    gmsh.clear()
    gmsh.finalize()


def test_ModelPart_associate_child_to_parent():
    """
    Test if the ModelPart associate_child_to_parent function works correctly.

    """
    gmsh.initialize()
    cube_child_tag = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    gmsh.model.occ.synchronize()
    model_part = ModelPart("cube_parent")
    model_part.associate_child_to_parent((3, cube_child_tag))

    # assert correct number of associated entities
    assert len(model_part.volume_tag) == 1
    assert len(model_part.surfaces_tags) == 6
    assert len(model_part.lines_tags) == 12
    assert len(model_part.points_tags) == 8

    gmsh.clear()
    gmsh.finalize()


def test_ModelPart_clean_inside_entities():
    """
    Test if the ModelPart clean_inside_entities function works correctly.

    """
    gmsh.initialize()
    final_domain_tag = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    gmsh.model.occ.synchronize()
    final_domain = ModelPart("fluid")
    final_domain.associate_child_to_parent((3, final_domain_tag))

    cube_child_tag = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
    gmsh.model.occ.synchronize()

    model_part = ModelPart("cube_parent")
    model_part.associate_child_to_parent((3, cube_child_tag))
    model_part.clean_inside_entities(final_domain)

    # assert correct number of cleaned inside entities
    assert len(model_part.surfaces_tags) == 0
    assert len(model_part.lines_tags) == 0
    assert len(model_part.points_tags) == 0

    gmsh.clear()
    gmsh.finalize()


def test_assignation():
    """
    Test if the assignation mechanism is correct on all parts
    test if the assignation of the entities of wing1 is correct

    """

    if TEST_OUT_PATH.exists():
        shutil.rmtree(TEST_OUT_PATH)
    TEST_OUT_PATH.mkdir()

    cpacs = CPACS(CPACS_IN_PATH)

    export_brep(cpacs, TEST_OUT_PATH)

    _, aircraft_parts = generate_gmsh(
        CPACS_IN_PATH,
        TEST_OUT_PATH,
        TEST_OUT_PATH,
        open_gmsh=False,
        farfield_factor=5,
        symmetry=False,
        mesh_size_farfield=5,
        mesh_size_fuselage=0.5,
        mesh_size_wings=0.5,
        refine_factor=1.0,
        auto_refine=False,
        testing_gmsh=False,
    )

    fuselage1_child = set([(3, 2)])
    wing1_m_child = set([(3, 5)])

    wing1_child = set([(3, 3)])
    wing1_volume_tag = [3]
    wing1_surfaces_tags = [5, 6, 7, 12, 13, 14, 19]
    wing1_lines_tags = [32, 33, 34, 7, 8, 9, 15, 16, 17, 18, 19, 20, 29, 30, 31]
    wing1_points_tags = [5, 6, 7, 12, 13, 14, 19, 20, 21]

    for part in aircraft_parts:
        if part.uid == "Wing_mirrored":
            assert part.children_dimtag == wing1_m_child
        if part.uid == "SimpleFuselage":
            assert part.children_dimtag == fuselage1_child
        if part.uid == "Wing":
            assert part.children_dimtag == wing1_child
            assert part.volume_tag == wing1_volume_tag
            assert part.surfaces_tags == wing1_surfaces_tags
            assert part.lines_tags == wing1_lines_tags
            assert part.points_tags == wing1_points_tags

    # Delete files generated by the test
    files_to_delete = [p for p in TEST_OUT_PATH.iterdir() if p.suffix in [".brep", ".su2"]]
    for file in files_to_delete:
        file.unlink()


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Test CPACS2GMSH")
    print("To run test use the following command:")
    print(">> pytest -v")
