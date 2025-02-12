from memories-dev.vortx import memories-dev
from memories-dev.models import DeepSeekR1, DeepSeekV3

def main():
    vortx = Vortx(models={'reasoning': DeepSeekR1(), 'vision': DeepSeekV3()})
    result = vortx.create_memories((34.0522, -118.2437), ('2024-04-01', '2024-04-30'))
    print(result)

if __name__ == "__main__":
    main() 