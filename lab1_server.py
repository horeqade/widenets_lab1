import socket
from math import floor, log2

from bitarray import bitarray


def encode(txt: str):
    ba = bitarray()
    ba.frombytes(txt.encode('utf-8'))
    return ba


def decode(txt: bitarray()):
    return txt.tobytes().decode('utf-8', 'ignore')


def byte2bit(b: bytes):
    ba = bitarray()
    ba.frombytes(b)
    return ba


def bit2byte(b: bitarray):
    return b.tobytes()


def noOfParityBitsInCode(noOfBits):
    i = 0
    while 2. ** i <= noOfBits:
        i += 1

    return i


def hammingCorrection(data):
    cnt1Err, cntCorrectDecode, cntIncorrectDecode = 0, 0, 0
    n = noOfParityBitsInCode(len(data))
    i = 0
    list1 = list(data)
    errorthBit = 0
    while i < n:
        k = 2. ** i
        j = 1
        total = 0
        while j * k - 1 < len(list1):
            if j * k - 1 == len(list1) - 1:
                lower_index = j * k - 1
                temp = list1[int(lower_index):len(list1)]
            elif (j + 1) * k - 1 >= len(list1):
                lower_index = j * k - 1
                temp = list1[int(lower_index):len(list1)]
            elif (j + 1) * k - 1 < len(list1) - 1:
                lower_index = (j * k) - 1
                upper_index = (j + 1) * k - 1
                temp = list1[int(lower_index):int(upper_index)]

            total = total + sum(int(e) for e in temp)
            j += 2
        if total % 2 > 0:
            errorthBit += k
        i += 1
    if errorthBit >= len(list1):
        cntIncorrectDecode += 1
    elif errorthBit >= 1:
        if list1[int(errorthBit - 1)] == 0:
            list1[int(errorthBit - 1)] = 1
        else:
            list1[int(errorthBit - 1)] = 0
        cnt1Err += 1
        cntCorrectDecode += 1
    else:
        cntCorrectDecode += 1
    list2 = list()
    i = 0
    j = 0
    k = 0
    while i < len(list1):
        if i != ((2 ** k) - 1):
            temp = list1[int(i)]
            list2.append(temp)
            j += 1
        else:
            k += 1
        i += 1
    return cnt1Err, cntCorrectDecode, cntIncorrectDecode, bitarray(list2)


def ham_decode(encoded: bitarray):
    encoded_length = len(encoded)
    num_parity_bits = floor(log2(
        encoded_length - 1)) + 1
    index_of_error = 0

    decoded = _extract_data(encoded)

    overall_expected = _calculate_parity(encoded[1:], 0)
    overall_actual = encoded[0]
    overall_correct = overall_expected == overall_actual

    for parity_bit_index in _powers_of_two(num_parity_bits):
        expected = _calculate_parity(decoded, parity_bit_index)
        actual = encoded[parity_bit_index]
        if not expected == actual:
            index_of_error += parity_bit_index

    # report results
    cnt1Err, cntCorrectDecode, cntIncorrectDecode = 0, 0, 0
    if index_of_error and overall_correct:
        cntIncorrectDecode += 1
    elif index_of_error and not overall_correct:
        cnt1Err += 1
        cntCorrectDecode += 1
        encoded[index_of_error] = not encoded[index_of_error]
    else:
        cntCorrectDecode += 1
    decoded = _extract_data(encoded)
    return cnt1Err, cntCorrectDecode, cntIncorrectDecode, decoded


def _extract_data(encoded: bitarray):
    data = bitarray()
    for i in range(3, len(encoded)):
        if not _is_power_of_two(i):
            data.append(encoded[i])
    return data


def _powers_of_two(n: int):
    power, i = 1, 0
    while i < n:
        yield power
        power <<= 1
        i += 1
    return None


def _calculate_parity(data: bitarray, parity: int):
    retval = 0  # 0 is the XOR identity

    if parity == 0:  # special case - compute the overall parity
        for bit in data:
            retval ^= bit
    else:
        for data_index in _data_bits_covered(parity, len(data)):
            retval ^= data[data_index]
    return retval


def _data_bits_covered(parity: int, lim: int):
    if not _is_power_of_two(parity):
        raise ValueError("All hamming parity bits are indexed by powers of two.")

    # use 1-based indexing for simpler computational logic
    data_index = 1  # bit we're currently at in the DATA bitstring
    total_index = 3  # bit we're currently at in the OVERALL bitstring

    while data_index <= lim:
        curr_bit_is_data = not _is_power_of_two(total_index)
        if curr_bit_is_data and (total_index % (parity << 1)) >= parity:
            yield data_index - 1  # adjust output to be zero indexed
        data_index += curr_bit_is_data
        total_index += 1
    return None


def _is_power_of_two(n: int):
    return (not (n == 0)) and ((n & (n - 1)) == 0)


def int_to_bytes(x: int) -> bytes:
    return x.to_bytes(10, 'big')


def int_from_bytes(xbytes: bytes) -> int:
    return int.from_bytes(xbytes, 'big')


def bytes_hamming_bytes(bytes, len_word=78):
    bits = byte2bit(bytes)
    hamming = []
    tot1Err, totCorrDecode, totIncorrDecode = 0, 0, 0
    for i in range(int(len(bits) / len_word) + 1):
        if i == int(len(bits) / len_word):
            cnt1Err, cntCorrectDecode, cntIncorrectDecode, arr = ham_decode(bits[i * len_word:])
            hamming.append(arr)
            tot1Err += cnt1Err
            totCorrDecode += cntCorrectDecode
            totIncorrDecode += cntIncorrectDecode
            continue
        cnt1Err, cntCorrectDecode, cntIncorrectDecode, arr = ham_decode(bits[i * len_word: (i + 1) * len_word])
        hamming.append(arr)
        tot1Err += cnt1Err
        totCorrDecode += cntCorrectDecode
        totIncorrDecode += cntIncorrectDecode

    hamming = bitarray(bit for ham in hamming for bit in ham)
    return tot1Err, totCorrDecode, totIncorrDecode, bit2byte(hamming)


def launch_server():
    sock = socket.socket()
    sock.bind(('', 9090))
    sock.listen(1)
    while True:
        conn, addr = sock.accept()
        print(f"connected with: {addr}")
        data = conn.recv(100000)
        print(f"{addr} data recieved")
        tot1Err, totCorrDecode, totIncorrDecode, decoded_bytes = bytes_hamming_bytes(data)
        print("Message decoded")
        stat_bytes = int_to_bytes(tot1Err) + int_to_bytes(totCorrDecode) + int_to_bytes(totIncorrDecode)

        conn.send(stat_bytes + decoded_bytes)

        conn.close()


if __name__ == '__main__':
    launch_server()
