from jobshoplab.compiler.mapper import DictToInitStateMapper, DictToInstanceMapper


def test_instance_mapping(minimal_instance_dict, default_instance, config):
    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(minimal_instance_dict)
    assert mapped_instance.machines == default_instance.machines
    assert mapped_instance.buffers == default_instance.buffers
    assert mapped_instance.transports == default_instance.transports
    assert mapped_instance.instance == default_instance.instance
    assert mapped_instance.description == default_instance.description
    assert mapped_instance.logistics == default_instance.logistics


def test_state_mapping(minimal_instance_dict, default_instance, config, default_init_state):
    mapper = DictToInitStateMapper("debug", config=config)
    mapped_state = mapper.map(minimal_instance_dict, default_instance)
    assert default_init_state.buffers == mapped_state.buffers
    assert default_init_state.transports == mapped_state.transports
    assert default_init_state.machines == mapped_state.machines
    assert default_init_state.jobs == mapped_state.jobs
    assert default_init_state.time == mapped_state.time


def test_instance_mapping_with_intralogistics(
    minimal_instance_dict_with_intralogistics, default_instance_with_intralogistics, config
):
    mapper = DictToInstanceMapper(0, config=config)
    mapped_instance = mapper.map(minimal_instance_dict_with_intralogistics)
    assert mapped_instance.machines == default_instance_with_intralogistics.machines
    assert mapped_instance.buffers == default_instance_with_intralogistics.buffers
    assert mapped_instance.transports == default_instance_with_intralogistics.transports
    assert mapped_instance.instance == default_instance_with_intralogistics.instance
    assert mapped_instance.description == default_instance_with_intralogistics.description
    assert mapped_instance.logistics == default_instance_with_intralogistics.logistics


def test_state_mapping_with_intralogistics(
    minimal_instance_dict_with_intralogistics, default_instance, config, default_init_state
):
    mapper = DictToInitStateMapper("debug", config=config)
    mapped_state = mapper.map(minimal_instance_dict_with_intralogistics, default_instance)
    assert default_init_state.buffers == mapped_state.buffers
    assert default_init_state.machines == mapped_state.machines
    assert default_init_state.jobs == mapped_state.jobs
    assert default_init_state.time == mapped_state.time

    # JUST TESTING AGAINST LOCATION STRING
    for mapped_transport, location in zip(mapped_state.transports, ["m-1", "m-2", "m-2"]):
        assert mapped_transport.location.location == location


def test_outages():
    pass


def test_stochastic_machine_times():
    pass


def test_stochastic_transport_times():
    pass


def test_static_setup_times():
    pass


def test_stochastic_setup_times():
    pass
