import pytest
import json
import os
from ttboard.project_mux import DesignIndex, DangerLevel, Design

Default_danger = DangerLevel.SAFE
    
@pytest.fixture(scope="session")
def shuttle(pytestconfig):
    return pytestconfig.getoption("shuttle")

@pytest.fixture(scope="session")
def shuttlepath(pytestconfig):
    return pytestconfig.getoption("shuttlepath")

def check_design(des:Design, project:dict):
    
    project_idx = int(project['address'])
    clock_hz = 0
    if 'clock_hz' in project:
        clock_hz = int(project['clock_hz'])
    
    danger_level = Default_danger
    if 'danger_level' in project:
        danger_level = DangerLevel.string_to_level(project['danger_level'])
    
    assert des.project_index == project_idx
    assert des.clock_hz == clock_hz
    assert des.danger_level == danger_level
    

def get_indices(shuttle, shuttlepath):
    
    shuttle_json_file = os.path.join(shuttlepath, f'{shuttle}.json')
    shuttle_bin_file = os.path.join(shuttlepath, f'{shuttle}.json.{DesignIndex.SerializedBinSuffix}')
    
    assert os.path.exists(shuttle_json_file)
    assert os.path.exists(shuttle_bin_file)
    
    
    # going to do a 3-way comparison
    jsonIndex = DesignIndex(None, None)
    jsonIndex.load_available(shuttle_json_file, force_json=True)
    
    binIndex = DesignIndex(None, None)
    binIndex.load_serialized(shuttle_bin_file)
    
    return (jsonIndex, binIndex)


def test_check_serialization(shuttle, shuttlepath):
    
    assert len(shuttle)
    assert len(shuttlepath)
    
    print(f"\nRunning test for shuttle: ***{shuttle}***\n")
    shuttle_json_file = os.path.join(shuttlepath, f'{shuttle}.json')
    (jsonIndex, binIndex) = get_indices(shuttle, shuttlepath)
    
    emptyIndex = DesignIndex(None, None)
    
    with open(shuttle_json_file) as fh:
        index = json.load(fh)
        for project in index['projects']:
            # some munging happens, get the resulting name
            project_name = emptyIndex.clean_project_name(project)
            
            
            # both should have the same number of matches
            bin_found = binIndex.find(project_name)
            assert len(bin_found)
            json_found = jsonIndex.find(project_name)
            assert len(json_found) == len(bin_found)
            
            
            danger_level = Default_danger
            if 'danger_level' in project:
                danger_level = DangerLevel.string_to_level(project['danger_level'])
            
            if danger_level >= DangerLevel.HIGH:
                print(f'{project_name}: HIGH danger')
                assert not jsonIndex.is_available(project_name)
                assert not binIndex.is_available(project_name)
            else:
                #print(f"project: {project_name} ({project['macro']})")
                assert jsonIndex.is_available(project_name)
                assert binIndex.is_available(project_name)
                # ok, found in both, now check values
                check_design(binIndex.get(project_name), project)
                check_design(jsonIndex.get(project_name), project)
            

