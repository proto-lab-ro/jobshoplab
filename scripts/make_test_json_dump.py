from jobshopsimulation.utils.utils import make_json_dump

from jobshoplab import JobShopLabEnv


def make_dump(dir="./tmp/test_dump.json"):
    env = JobShopLabEnv()
    while not env.done:
        env.step(1)
    make_json_dump(env.history, env.instance, env.loglevel, dir=dir)


if __name__ == "__main__":
    make_dump()
