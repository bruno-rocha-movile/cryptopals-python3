import challenge52
import util

def findNBlockPrefixCollision(hashFn, iv, blockLength, n):
    prefix = b'\x00' * (blockLength * (n-1))
    prefixHash = hashFn(prefix, iv, pad=False)
    hashToLastBlock = {}
    for s in (i.to_bytes(blockLength, byteorder='little') for i in range(2**(blockLength*8))):
        h = hashFn(s, iv, pad=False)
        if h in hashToLastBlock:
            return (h, s, prefix + hashToLastBlock[h])

        h = hashFn(s, prefixHash, pad=False)
        hashToLastBlock[h] = s
    raise Exception('unexpected')

def makeExpandablePrefix(hashFn, iv, blockLength, k):
    blocks = []
    state = iv
    for i in range(k):
        state, s, nBlock = findNBlockPrefixCollision(hashFn, state, blockLength, 2**(k-1-i)+1)
        blocks += [[s, nBlock]]
    return state, blocks

def makeExpandedPrefix(blockSize, blocks, k, l):
    m = b''
    for i in range(len(blocks)):
        block = blocks[i]
        if len(m) // blockSize + len(block[1]) // blockSize + (len(blocks) - i - 1) <= l:
            nextSegment = block[1]
        else:
            nextSegment = block[0]
        m += nextSegment
    if len(m) // blockSize != l:
        raise Exception('unexpected')
    return m

def getIntermediateStates(m, hashFn, iv, blockLength):
    state = iv
    for block in (m[blockLength*i:blockLength*(i+1)] for i in range(len(m) // blockLength)):
        state = hashFn(block, state, pad=False)
        yield state

def findIntermediateStateCollision(hashFn, iv, blockLength, hashLength, intermediateStateIter, minBlockCount):
    statesToIndices = {}
    i = 0
    for state in intermediateStateIter:
        if i >= minBlockCount:
            statesToIndices[state] = i
        i += 1

    if not statesToIndices:
        raise Exception('unexpected')

    for s in (i.to_bytes(blockLength, byteorder='little') for i in range(2**(blockLength*8))):
        h = hashFn(s, iv, pad=False)
        if h in statesToIndices:
            return s, statesToIndices[h]

    raise Exception('unexpected')

def findSecondPreimage(m, hashFn, iv, blockLength, hashLength):
    blockCount = (len(m) + blockLength - 1) // blockLength
    k = blockCount.bit_length()
    prefixState, blocks = makeExpandablePrefix(hashFn, iv, blockLength, k)

    intermediateStateIter = getIntermediateStates(m, hashFn, iv, blockLength)
    bridge, collisionBlockCount = findIntermediateStateCollision(hashFn, prefixState, blockLength, hashLength, intermediateStateIter, k)

    m2 = makeExpandedPrefix(blockLength, blocks, k, collisionBlockCount) + bridge
    m2 += m[len(m2):]
    return m2

if __name__ == '__main__':
    m = util.randbytes(100)
    h = challenge52.badHash(m, b'')
    m2 = findSecondPreimage(m, challenge52.badHash, b'', challenge52.badHashBlockLength, challenge52.badHashHashLength)
    h2 = challenge52.badHash(m2, b'')
    print(m, m2, h, h2)
    if len(m2) != len(m):
        raise Exception('{0} != {1}'.format(len(m2), len(m)))
    if h2 != h:
        raise Exception(h2 + b' != ' + h)
