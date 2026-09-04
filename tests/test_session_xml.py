from scientific_visualization.session import save_xml_session, load_xml_session


def test_xml_session_roundtrip(tmp_path):
    state = {'files':['a.h5','b.h5'], 'current_index':1, 'view_xlim':[0.2,4.0], 'camera_position':[1,2,3], 'settings':{'direction':'(x,y,z)','enabled':True}}
    path=tmp_path/'session.xml'; save_xml_session(path,state)
    restored=load_xml_session(path)
    assert restored['files']==state['files']
    assert restored['current_index']=='1'
    assert restored['camera_position']==['1','2','3']
    assert restored['settings']['direction']=='(x,y,z)'
    assert restored['settings']['enabled']=='True'
