def test_nonrentrant_decorator(get_contract, assert_tx_failed):
    calling_contract_code = """
interface SpecialContract:
    def unprotected_function(val: string[100], do_callback: bool): nonpayable
    def protected_function(val: string[100], do_callback: bool): nonpayable
    def special_value() -> string[100]: nonpayable

@public
def updated():
    SpecialContract(msg.sender).unprotected_function('surprise!', False)

@public
def updated_protected():
    SpecialContract(msg.sender).protected_function('surprise protected!', False)  # This should fail.  # noqa: E501
    """

    reentrant_code = """
interface Callback:
    def updated(): nonpayable
    def updated_protected(): nonpayable

special_value: public(string[100])
callback: public(Callback)

@public
def set_callback(c: address):
    self.callback = Callback(c)

@public
@nonreentrant('protect_special_value')
def protected_function(val: string[100], do_callback: bool) -> uint256:
    self.special_value = val

    if do_callback:
        self.callback.updated_protected()
        return 1
    else:
        return 2

@public
def unprotected_function(val: string[100], do_callback: bool):
    self.special_value = val

    if do_callback:
        self.callback.updated()
    """

    reentrant_contract = get_contract(reentrant_code)
    calling_contract = get_contract(calling_contract_code)

    reentrant_contract.set_callback(calling_contract.address, transact={})
    assert reentrant_contract.callback() == calling_contract.address

    # Test unprotected function.
    reentrant_contract.unprotected_function("some value", True, transact={})
    assert reentrant_contract.special_value() == "surprise!"

    # Test protected function.
    reentrant_contract.protected_function("some value", False, transact={})
    assert reentrant_contract.special_value() == "some value"

    assert_tx_failed(lambda: reentrant_contract.protected_function("zzz value", True, transact={}))
