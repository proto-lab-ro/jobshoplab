# import pytest

# # from jobshoplab.compiler.validators import Validator
# from jobshoplab.utils.exceptions import InvalidKey, InvalidType, InvalidValue


# def test_instance_correctness(minimal_instance_dict, config):
#     wrong_instance_dict0 = {
#         "instance_config": {
#             "description": "3x3",
#             "instance": {
#                 "specification": """
#                     3 3
#                     0 3 2 2 1 2
#                     0 2 1 4 2 1
#                     1 4 2 3 0 3
#                     """
#             },
#         }
#     }
#     wrong_instance_dict1 = {
#         "instance_config": {
#             "description": "3x3",
#             "instance": {
#                 "specification": """

#                     """
#             },
#         }
#     }

#     wrong_instance_dict2 = {
#         "instance_config": {
#             "description": "3x3",
#             "instance": {
#                 "specification": """
#                     (m,t)|(m1,t)|(m2,t)
#                     j0|(0,3) (1,2) (2,2)
#                     j1|(0,2) (2,1) (1,4)
#                     j2|(1,4) (2,3) (0,3)
#                 """
#             },
#         }
#     }
#     wrong_instance_dict3 = {
#         "instance_config": {
#             "description": "3x3",
#             "instance": {
#                 "specification": """
#                     (m0,t)|(m1,t)|(m2,t)
#                     j0|(3,3) (1,2) (2,2)
#                     j1|(0,2) (2,1) (1,4)
#                     j2|(1,4) (2,3) (0,3)
#                 """
#             },
#         }
#     }

#     vali = Validator("debug", config)
#     with pytest.raises(InvalidValue):
#         vali(wrong_instance_dict0)
#         vali(wrong_instance_dict1)
#         vali(wrong_instance_dict2)
#         vali(wrong_instance_dict3)

#     try:
#         vali(minimal_instance_dict)
#     except InvalidValue:
#         pytest.fail("Validation failed on correct instance")


# def test_field_name_correctness(minimal_instance_dict, config):
#     wrong = {
#         "instance_config": {
#             "description": "3x3",
#             "instance": {
#                 "spec": """
#                     (m0,t)|(m1,t)|(m2,t)
#                     j0|(2,3) (1,2) (2,2)
#                     j1|(0,2) (2,1) (1,4)
#                     j2|(1,4) (2,3) (0,3)
#                 """
#             },
#         }
#     }

#     vali = Validator("debug", config)
#     with pytest.raises(InvalidKey):
#         vali(wrong)
#     try:
#         vali(minimal_instance_dict)
#     except InvalidKey:
#         pytest.fail("Validation failed on correct instance")


# def test_has_field(minimal_instance_dict, config):
#     wrong = {
#         "instance_config": {
#             "description": "3x3",
#         }
#     }

#     vali = Validator("debug", config)
#     with pytest.raises(InvalidKey):
#         vali(wrong)
#     try:
#         vali(minimal_instance_dict)
#     except InvalidKey:
#         pytest.fail("Validation failed on correct instance")


# def test_field_type_correctness(minimal_instance_dict, config):
#     wrong = {
#         "instance_config": {
#             "description": 3,
#             "instance": {
#                 "specification": """
#                     (m0,t)|(m1,t)|(m2,t)
#                     j0|(2,3) (1,2) (2,2)
#                     j1|(0,2) (2,1) (1,4)
#                     j2|(1,4) (2,3) (0,3)
#                 """
#             },
#         }
#     }
#     with pytest.raises(InvalidType):
#         vali = Validator("debug", config)
#         vali(wrong)
#     try:
#         vali(minimal_instance_dict)
#     except InvalidValue:
#         pytest.fail("Validation failed on correct instance")


# def test_description_checking(minimal_instance_dict, config):
#     wrong = {
#         "instance_config": {
#             "instance": {
#                 "specification": """
#                     (m0,t)|(m1,t)|(m2,t)
#                     j0|(2,3) (1,2) (2,2)
#                     j1|(0,2) (2,1) (1,4)
#                     j2|(1,4) (2,3) (0,3)
#                 """
#             },
#         }
#     }
#     vali = Validator("debug", config)
#     with pytest.raises(InvalidValue):
#         vali(wrong)
#     try:
#         vali(minimal_instance_dict)
#     except InvalidValue:
#         pytest.fail("Validation failed on correct instance")
